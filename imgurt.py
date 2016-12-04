#!/bin/env python3
## Evan Widloski - 2016-12-03
## Imgurt - Imgur wallpaper ranker and changer
## Uses logistic function to choose wallpaper based
##   on number of views, resolution and aspect ratio

import requests
import logging
import random
import math
import sys
from subprocess import Popen, PIPE
import json
from datetime import datetime, timedelta

# search for images with this aspect ratio and resolution
screen_width = 1600
screen_height = 900

# search these subreddits (via Imgur)
subreddits = ["winterporn", "earthporn", "natureporn"]
sfw_only = True
# allow an image to be selected more than once
unseen_only = False

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
pixel_cutoff = .75  # image pixels / screen pixels

# discrimination factor - controls steepness at cutoff point
ratio_k = 10
views_k = 5
pixel_k = 5

# weight - importance of parameter when selecting an image
# note: these are automatically normalized, so their magnitude doesn't matter
ratio_weight = 3
views_weight = 1
pixel_weight = 3

# maximum number of pages of images to load for 1 subreddit
max_pages = 5
url = "https://api.imgur.com/3/gallery/r/{0}/top/year/{1}"
album_url = "https://api.imgur.com/3/album/{0}"
# imgur api id
client_id = "5f21952153b5f6c"
headers = {"Authorization":"Client-ID {0}".format(client_id)}

# store scored images
cache_file = '/tmp/imgurt_cache'
# set cache to expire after 1 week
cache_expiry = timedelta(days=7)
# use ctime format for storing cache date
date_format = "%a %b %d %H:%M:%S %Y"
# update cache when these options change
options = [sfw_only, subreddits, screen_width, screen_height, ratio_cutoff,
           views_cutoff, pixel_cutoff, ratio_k, views_k, pixel_k, ratio_weight,
           views_weight, pixel_weight, url]

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
# hide annoying requests messages
logging.getLogger("requests").setLevel(logging.WARNING)


# score each image based on parameters
# higher score is better
def score(images):
    max_views = max([image['views'] for image in images])
    screen_pixels = screen_width * screen_height
    screen_ratio = float(screen_width)/screen_height

    for image in images:
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
        image_pixels = image['width'] * image['height']
        pixel_score = float(image_pixels) / screen_pixels
        if pixel_score > 1:
            pixel_score = 1

        # Calculate final image score from presets.
        # scores.append(  1/(1 + pow(math.e, -ratio_k * (ratio_score - ratio_cutoff)))
        #                 * ratio_weight
        #               + 1/(1 + pow(math.e, -views_k * (views_score - views_cutoff)))
        #                 * views_weight
        #               + 1/(1 + pow(math.e, -pixel_k * (pixel_score - pixel_cutoff)))
        #                 * pixel_weight)
        image['imgurt_score'] = (1/(1 + pow(math.e, -ratio_k * (ratio_score - ratio_cutoff))) *
                                 1/(1 + pow(math.e, -views_k * (views_score - views_cutoff))) *
                                 1/(1 + pow(math.e, -pixel_k * (pixel_score - pixel_cutoff))))

def get_images(subreddits, seen = None):

    # get list of images and albums for each subreddit

    # get results for each subreddit
    results = []
    for subreddit in subreddits:
        # keep getting results on each subreddit album until there are none left
        page_num = 0
        while page_num < max_pages:
            page_url = url.format(subreddit, page_num)
            logging.debug("Downloading page #{0} from subreddit {1}".format(page_num, subreddit))
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

    # mark images as unseen
    for image in images:
        image['seen'] = False

    # make sure we actually got results
    if len(images) == 0:
        logging.info("No results found")
        sys.exit()

    return images


# select a random image weighted by score
def weighted_select(images):
    # if unseen_only is true, only look at at unseen images
    total_imgurt_score = sum([image['imgurt_score'] for image in images if not (unseen_only and image['seen'])])
    rand_score = random.uniform(0, total_imgurt_score)
    for image in images:
        if unseen_only and image['seen']:
            continue
        rand_score -= image['imgurt_score']
        if rand_score <= 0:
            break

    logging.info("Selected {0} with score {1} out of {2} images".format(image['link'], image['imgurt_score'], len(images)))
    logging.info("The probability of selecting this image was {0}".format(image['imgurt_score']/total_imgurt_score))

    # set selected image as seen
    image['seen'] = True

    # write to cache file
    date = datetime.strftime(datetime.now(), date_format)
    f = open(cache_file, 'w')
    f.write(json.dumps({'date': date,
                        'images': images,
                        'options': options}, indent=4))
    return image


# set wallpaper with feh
def set_wallpaper(image):
    logging.info("Applying wallpaper")

    # download image and send to feh stdin

    response = requests.get(image['link'])
    p = Popen(['feh', '-', '--bg-fill'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    logger.debug("feh response: {0}".format(p.communicate(input=(response.content))))

# update image cache
def update_cache():

    return images


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
            score(images)
        # otherwise, fetch scored images from cache
        else:
            images = j['images']

    # if cache is not found, create it
    except IOError:
        logging.info("No cache found at {0}.  Creating...".format(cache_file))
        images = get_images(subreddits)
        score(images)

    # select image and set as wallpaper
    image = weighted_select(images)
    set_wallpaper(image)
