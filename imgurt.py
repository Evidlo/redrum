#!/bin/env python3
# -*- coding: utf-8 -*-

## Evan Widloski - 2016-12-03
## Imgurt - Imgur wallpaper ranker and changer
## Uses logistic function to choose wallpaper based
##   on number of views, resolution and aspect ratio

import requests
from requests.exceptions import ConnectionError
import logging
import random
import math
import sys
import os
from subprocess import Popen, PIPE
import json
from datetime import datetime, timedelta

# search for images with this aspect ratio and resolution
screen_width = 1600
screen_height = 900
screen_ratio = float(screen_width)/screen_height

# search these subreddits (via Imgur)
subreddits = ["winterporn", "earthporn", "natureporn", "spaceporn"]
sfw_only = True
# don't select previously selected images
unseen_only = True

# Use logistic function to give nonlinear discrimination between good and bad matches.
#   see https://en.wikipedia.org/wiki/Logistic_function
#
#                                               weight -->  ‚------
#                       1                                  /
#   f(x) = ----------------------------                   /  <-- k (steepness)
#            1 + e^(-k(x - cutoff))                      /
#                                       0 -  -  - ------‘ ∧ -  -  -  -  -  -
#                                                         |
#                                                      cutoff

# cutoff - set this about halfway between what you would consider a good and bad value
# eg. if an image having 60% of the pixels of the screen is unacceptable
#     but 90% is acceptable, set pixel_cutoff to .75
# note: must be in range 0-1
ratio_cutoff = .95  # keep this high to avoid cutting off edges of image
views_cutoff = .75  # image views percentile
pixel_cutoff = 1  # image pixels / screen pixels

# discrimination factor - controls steepness at cutoff point
ratio_k = 15
views_k = 2
pixel_k = 35 # set high for a very sharp threshold

# maximum number of pages of images to load for 1 subreddit
max_pages = 10
url = "https://api.imgur.com/3/gallery/r/{0}/top/all/{1}"
album_url = "https://api.imgur.com/3/album/{0}"
# imgur api id
client_id = "5f21952153b5f6c"
headers = {"Authorization":"Client-ID {0}".format(client_id)}

# store scored images
cache_file = os.path.expanduser('~/.cache/imgurt_cache')
# set cache to expire after 1 week
cache_expiry = timedelta(days=7)
# use ctime format for storing cache date
date_format = "%a %b %d %H:%M:%S %Y"
# update cache when these options change
options = [sfw_only, subreddits, screen_width, screen_height, ratio_cutoff,
           views_cutoff, pixel_cutoff, ratio_k, views_k, pixel_k, max_pages, url]

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
# hide annoying requests messages
logging.getLogger("requests").setLevel(logging.WARNING)

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


def get_images(subreddits):

    # get list of images and albums for each subreddit

    # get results for each subreddit
    results = []
    for subreddit in subreddits:
        # keep getting results on each subreddit album until there are none left
        page_num = 0
        while page_num < max_pages:
            page_url = url.format(subreddit, page_num)
            logging.info("Downloading page #{0} from subreddit {1}".format(page_num, subreddit))
            response = requests.get(page_url, headers=headers)
            page_results = response.json()['data']
            page_num += 1

            # once we hit the last page, break
            if len(page_results) == 0:
                break

            results += page_results

        if page_num == 0:
            logging.info("No results found for subreddit {0}.".format(subreddit))

    # clean list of images and albums

    # build list of images, replacing albums with images they contain
    images = []
    for result in results:
        # if result is an album, append its images to `images`
        if result['is_album']:
            album_id = result['id']
            logging.debug("Unpacking album {0}".format(album_id))
            response = requests.get(album_url.format(album_id), headers=headers)
            album_results = response.json()['data']

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
    f = open(cache_file, 'w')
    f.write(json.dumps({'date': date,
                        'options': options,
                        'seen':seen,
                        'images': images}, indent=4))
    f.close()

if __name__ == "__main__":
    # attempt to load scored images from cache
    try:
        f = open(cache_file, 'r')
        j = json.loads(f.read())
        logging.info("Found cache at {0}".format(cache_file))
        date = j['date']
        # if the cache is old or `options` has changed, update it
        if ((datetime.now() - datetime.strptime(date, date_format)) > cache_expiry or
                j['options'] != options):
            logging.info("Detected old cache. Updating...")
            images = get_images(subreddits)
            date = datetime.now().strftime(date_format)

        # otherwise, fetch scored images from cache
        else:
            images = j['images']

        seen = j['seen']

    # if cache is not found, create it
    except IOError:
        logging.info("No cache found at {0}.  Creating...".format(cache_file))
        date = datetime.strftime(datetime.now(), date_format)
        images = get_images(subreddits)
        seen = []

    max_views = max([image['views'] for image in images])

    # score each image based on parameters
    # higher score is better
    for image in images:

        # Calculate final image score from presets.
        image['imgurt_score'] = score_image(image, max_views)[0]

    # select image and set as wallpaper
    image = weighted_select(images, seen)
    seen.append(image['id'])

    set_wallpaper(image)
    save(images, date, seen, options)
