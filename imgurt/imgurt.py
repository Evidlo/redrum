#!/bin/env python3
# -*- coding: utf-8 -*-

## Evan Widloski - 2016-12-03
## Imgurt - Imgur wallpaper ranker and changer
## Uses logistic function to choose wallpaper based
##   on number of views, resolution and aspect ratio

import sys
if sys.version_info[0] == 2:
    sys.exit('Please install using pip3.')

import requests
from requests.exceptions import ConnectionError
import logging
import random, math
import os, shutil
from subprocess import Popen, PIPE
import json
from datetime import datetime, timedelta
from configparser import SafeConfigParser

module_path = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
# hide annoying requests messages
logging.getLogger("requests").setLevel(logging.WARNING)

# attempt to load settings from file
config_file = os.path.expanduser('~/.config/imgurt.ini')

if not os.path.exists(config_file):
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    logging.info("No config found at {0}.  Installing...".format(config_file))
    shutil.copyfile(module_path + '/imgurt.ini', config_file)

parser = SafeConfigParser()
parser.read(config_file)
config = parser['imgurt']

screen_width = config.getint('screen_width', 1600)
screen_height = config.getint('screen_height', 900)
screen_ratio = float(screen_width)/screen_height

subreddits = config.get('subreddits').split('\n')
sfw_only = config.getboolean('sfw_only', True)
unseen_only = config.getboolean('unseen_only', True)

ratio_cutoff = config.getfloat('ratio_cutoff', .95)
views_cutoff = config.getfloat('views_cutoff', .75)
pixel_cutoff = config.getfloat('pixel_cutoff', 1)

ratio_k = config.getfloat('ratio_k', 15)
views_k = config.getfloat('views_k', 15)
pixel_k = config.getfloat('pixel_k', 15)

max_pages = config.getint('max_pages', 10)
url = config.get('url', "https://api.imgur.com/3/gallery/r/{0}/top/all/{1}")
album_url = config.get('album_url', "https://api.imgur.com/3/album/{0}")


# imgur downloading
client_id = config.get('client_id', "5f21952153b5f6c")
headers = {"Authorization": "Client-ID {0}".format(client_id)}

# where to store scored image metadata
cache_file = os.path.expanduser(config.get('cache_file', '~/.cache/imgurt_cache.json'))
# set cache to expire after 1 week
cache_expiry = timedelta(days=7)
# use ctime format for storing cache date
date_format = "%a %b %d %H:%M:%S %Y"
# update cache when these options change
options = [sfw_only, subreddits, screen_width, screen_height, ratio_cutoff,
           views_cutoff, pixel_cutoff, ratio_k, views_k, pixel_k, max_pages, url]

# calculate a score for an image
def score_image(image, max_views):
    # score image ratio match from 0-1
    # calculates quotient of ratio.  the closer to 1, the better the match
    image_ratio = float(image['width']) / image['height']
    if screen_ratio < image_ratio:
        ratio_score = screen_ratio / image_ratio
    else:
        ratio_score = image_ratio / screen_ratio

    # score total views from 0-1
    views_score = float(image['views']) / max_views

    # score image pixels from 0-1
    # don't give any extra weight to images greater than our screen size
    width_score = float(image['width']) / screen_width
    height_score = float(image['height']) / screen_height
    if width_score > 1:
        width_score = 1
    if height_score > 1:
        height_score = 1
    pixel_score = width_score * height_score

    # run the scores through logistic function
    ratio_logistic_score = 1/(1 + pow(math.e, -ratio_k * (ratio_score - ratio_cutoff)))
    views_logistic_score = 1/(1 + pow(math.e, -views_k * (views_score - views_cutoff)))
    pixel_logistic_score = 1/(1 + pow(math.e, -pixel_k * (pixel_score - pixel_cutoff)))

    final_score = ratio_logistic_score * views_logistic_score * pixel_logistic_score

    # `imgurt.py` only uses final_score, but `tune.py` also uses this function and needs the rest
    return [final_score,
            ratio_score,
            views_score,
            pixel_score,
            ratio_logistic_score,
            views_logistic_score,
            pixel_logistic_score]


# get list of image and album metadata from each subreddit
def get_images(subreddits):


    # get results for each subreddit
    results = []
    for subreddit in subreddits:
        # keep getting results on each subreddit album until there are none left
        page_num = 0
        while page_num < max_pages:
            page_url = url.format(subreddit, page_num)
            logging.info("Indexing page #{0} from subreddit {1}".format(page_num, subreddit))
            response = requests.get(page_url, headers=headers).json()

            if response['success'] == True:
                page_results = response['data']
                page_num += 1

                # once we hit the last page, break
                if len(page_results) == 0:
                    break

                results += page_results

            else:
                logging.error("Received error from Imgur: {0}".format(response['data']['error']))

        if page_num == 0:
            logging.info("No results found for subreddit {0}.".format(subreddit))

    # clean list of images and albums

    # build list of images, replacing albums with images they contain
    logging.info("Unpacking albums")
    images = []
    for result in results:
        # if result is an album, append its images to `images`
        if result['is_album']:
            album_id = result['id']
            logging.debug("Unpacking album {0}".format(album_id))
            response = requests.get(album_url.format(album_id), headers=headers).json()
            album_results = response['data']

            for image in album_results['images']:
                images.append(image)

        # else, append image
        else:
            images.append(result)

    # remove zero pixel (deleted) images
    images = [image for image in images if (image['width'] > 0 and image['height'] > 0)]

    # remove NSFW
    if sfw_only:
        images = [image for image in images if image['nsfw'] == False]

    # make sure we actually got results
    if len(images) == 0:
        logging.info("No results found")
        sys.exit()

    # score each image based on parameters
    # higher score is better
    logging.info("Scoring images")
    max_views = max([image['views'] for image in images])
    for image in images:

        # Calculate final image score from presets.
        image['imgurt_score'] = score_image(image, max_views)[0]

    return images


# select a random image weighted by score
def weighted_select(images, seen):
    # if unseen_only is true, only look at at unseen images
    if unseen_only:
        images = [image for image in images if image['id'] not in seen]

    if len(images) == 0:
        logging.info("No images available.  Set `unseen_only` to False, increase `max_pages` or add more subreddits")
        sys.exit()

    total_imgurt_score = sum([image['imgurt_score'] for image in images])
    rand_score = random.uniform(0, total_imgurt_score)
    for image in images:
        rand_score -= image['imgurt_score']
        if rand_score <= 0:
            break

    logging.info("Selected {0} ({1}) with score {2} out of {3} images".format(image['link'],
                                                                              image['section'],
                                                                              image['imgurt_score'],
                                                                              len(images)))
    logging.info("The probability of selecting this image was {0}".format(image['imgurt_score']/total_imgurt_score))

    # set selected image as seen
    image['seen'] = True

    return image


# set wallpaper with feh
def set_wallpaper(image):

    logging.info("Applying wallpaper")

    # download image and send to feh stdin
    try:
        response = requests.get(image['link'])
    except ConnectionError:
        logging.error("Connection error")
        quit()

    p = Popen(['feh', '-', '--bg-fill'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    logger.debug("feh response: {0}".format(p.communicate(input=(response.content))))


# save date, options, seen images and images to cache
def save(images, date, seen, options):

    # write to cache file
    if not os.path.exists(cache_file):
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as cache:
        cache.write(json.dumps({'date': date,
                            'options': options,
                            'seen':seen,
                            'images': images}, indent=4))

def main():
    # attempt to load scored images from cache
    if not os.path.exists(cache_file):
        logging.info("No previous score cache found at {0}.".format(cache_file))
        date = datetime.strftime(datetime.now(), date_format)
        images = get_images(subreddits)
        seen = []

    else:
        with open(cache_file, 'r') as cache:
            j = json.loads(cache.read())
            logging.info("Found cache at {0}".format(cache_file))
            date = j['date']
            # if the cache is old or `options` has changed, update it
            if ((datetime.now() - datetime.strptime(date, date_format)) > cache_expiry or
                    j['options'] != options):
                logging.info("Detected old cache. Updating...")
                # reload image metadata
                images = get_images(subreddits)
                date = datetime.now().strftime(date_format)

            # otherwise, fetch scored images from cache
            else:
                images = j['images']

        seen = j['seen']

    # select image and set as wallpaper
    image = weighted_select(images, seen)
    set_wallpaper(image)
    seen.append(image['id'])

    save(images, date, seen, options)

if __name__ == "__main__":
    main()
