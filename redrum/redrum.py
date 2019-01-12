#!/bin/env python3
# -*- coding: utf-8 -*-

## Evan Widloski - 2016-12-03
## redrum - Reddit wallpaper ranker and changer
## Uses logistic function to choose wallpaper based
##   on number of views, resolution and aspect ratio

from __future__ import print_function
import sys

# if sys.version_info[0] < 3:
#     sys.exit("redrum must be run in python3 (or installed through pip3.)")

import requests
from requests.exceptions import ConnectionError
import logging
import random, math
import os, shutil
import subprocess
import json
import argparse
from .version import __version__
from datetime import datetime, timedelta
from configparser import SafeConfigParser

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
# hide annoying requests messages
logging.getLogger("requests").setLevel(logging.WARNING)



def logistic_function(x, midpoint, k):
    return (1 + pow(math.e, -k * (1 - midpoint))) / (1 + pow(math.e, -k * (x - midpoint)))

# calculate a score for an image
def score_image(config, image, max_views):
    # score image ratio match from 0-1
    # calculates quotient of ratio.  the closer to 1, the better the match
    image_ratio = float(image['width']) / image['height']
    if config.screen_ratio < image_ratio:
        ratio_score = config.screen_ratio / image_ratio
    else:
        ratio_score = image_ratio / config.screen_ratio

    # score total views from 0-1
    views_score = float(image['views']) / max_views

    # score image pixels from 0-1
    # don't give any extra weight to images greater than our screen size
    width_score = float(image['width']) / config.screen_width
    height_score = float(image['height']) / config.screen_height
    if width_score > 1:
        width_score = 1
    if height_score > 1:
        height_score = 1
    pixel_score = width_score * height_score

    # run the scores through logistic function
    ratio_logistic_score = logistic_function(ratio_score, config.ratio_midpoint, config.ratio_k)
    views_logistic_score = logistic_function(views_score, config.views_midpoint, config.views_k)
    pixel_logistic_score = logistic_function(pixel_score, config.pixel_midpoint, config.pixel_k)

    final_score = ratio_logistic_score * views_logistic_score * pixel_logistic_score

    # `redrum.py` only uses final_score, but `tune.py` also uses this function and needs the rest
    return [final_score,
            ratio_score,
            views_score,
            pixel_score,
            ratio_logistic_score,
            views_logistic_score,
            pixel_logistic_score]

# get list of image and album metadata from each subreddit
def get_images(config):

    # get results for each subreddit
    results = []
    for subreddit in config.subreddits:
        # keep getting results on each subreddit album until there are none left
        page_num = 0
        while page_num < config.max_pages:
            page_url = config.url.format(subreddit, page_num)
            print("Indexing page {0} from subreddit {1}\r".format(', '.join(map(str, range(page_num + 1))), subreddit), end="")
            response = requests.get(page_url, headers=config.headers).json()

            if response['success'] == True:
                # tag all images with their subreddit
                for result in response['data']:
                    result['subreddit'] = subreddit
                page_results = response['data']
                page_num += 1

                # once we hit the last page, break
                if len(page_results) == 0:
                    break

                results += page_results

            else:
                logging.error("Received error from Imgur: {0}".format(response['data']['error']))

        if page_num == 0:
            logging.error("No results found for subreddit {0}.".format(subreddit))
        print()

    # clean list of images and albums
    def check_results(results, in_album=False):
        for result in results:
            logger.debug(result)
            # if result is an album, append its images to `images`
            if not in_album and result['is_album']:
                album_id = result['id']
                logging.debug("Unpacking album {0}".format(album_id))
                response = requests.get(config.album_url.format(album_id), headers=config.headers).json()
                if response['success'] == True:
                    album_results = response['data']
                    check_results(album_results['images'], in_album = True)
                else:
                    logging.error("Received error from Imgur: {0}".format(response['data']['error']))

            # remove zero pixel (deleted) images
            elif (result['width'] == 0 or result['height'] == 0):
                continue

            # remove NSFW
            elif config.sfw_only and result['nsfw'] == True:
                continue

            # else, append image
            else:
                images.append(result)

    # build list of images, replacing albums with images they contain
    print("Filtering results...")
    images = []
    check_results(results)

    # make sure we actually got results
    if len(images) == 0:
        print("No results found")
        sys.exit()

    # score each image based on parameters
    # higher score is better
    print("Scoring {} images".format(len(images)))
    max_views = max([image['views'] for image in images])
    for image in images:

        # Calculate final image score from presets.
        image['redrum_score'] = score_image(config, image, max_views)[0]

    return images


# select a random image weighted by score
def weighted_select(config, images, seen):
    # if unseen_only is true, only look at at unseen images
    if config.unseen_only:
        images = [image for image in images if image['id'] not in seen]

    if len(images) == 0:
        print("No images available.  Set `unseen_only` to False, increase `max_pages` or add more subreddits")
        sys.exit()

    total_redrum_score = sum([image['redrum_score'] for image in images])
    rand_score = random.uniform(0, total_redrum_score)
    for image in images:
        rand_score -= image['redrum_score']
        if rand_score <= 0:
            break

    print("Selected {0} ({1}) with score {2} out of {3} images".format(image['link'],
                                                                       image['subreddit'],
                                                                       image['redrum_score'],
                                                                       len(images)))
    print("The probability of selecting this image was {0}".format(image['redrum_score']/total_redrum_score))

    return image


# set wallpaper
def set_wallpaper(config, image):

    print("Applying wallpaper")

    # download image to `image`
    try:
        response = requests.get(image['link'])
        if response.status_code == 200:
            with open(config.image_file, 'wb') as f:
                f.write(response.content)
        else:
            logging.error("Got response {} when downloading image.".format(reponse.status_code))
    except ConnectionError:
        logging.error("Connection error")
        sys.exit()

    try:
        subprocess.check_output(config.wallpaper_command.format(image_file=config.image_file), shell=True)
    except subprocess.CalledProcessError as e:
        logger.error("Command `{}` failed with status {}".format(e.cmd, e.returncode))
        sys.exit()


# save date, options, seen images and images to cache
def save(config, images, date, seen):

    # write to cache file
    if not os.path.exists(config.cache_file):
        os.makedirs(os.path.dirname(config.cache_file), exist_ok=True)
    with open(config.cache_file, 'w') as cache:
        cache.write(json.dumps({'date': date,
                                'options': config.options,
                                'seen':seen,
                                'images': images}, indent=4))


class Config(object):
    def __init__(self, config_path):
        config_path = os.path.expanduser(config_path)

        # attempt to load settings from file
        if not os.path.exists(config_path):
            logging.info("No config found at {0}.  Creating...".format(config_path))
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            module_path = os.path.dirname(os.path.realpath(__file__))
            shutil.copyfile(module_path + '/redrum.ini', config_path)
            logging.info("Update config with your preferred options and run redrum again.")
            sys.exit()

        config_parser = SafeConfigParser()
        config_parser.read(config_path)
        config = config_parser['redrum']

        self.screen_width = config.getint('screen_width', 1600)
        self.screen_height = config.getint('screen_height', 900)
        self.screen_ratio = float(self.screen_width)/self.screen_height

        self.subreddits = config.get('subreddits').split('\n')
        self.sfw_only = config.getboolean('sfw_only', True)
        self.unseen_only = config.getboolean('unseen_only', True)

        self.ratio_midpoint = config.getfloat('ratio_midpoint', .95)
        self.views_midpoint = config.getfloat('views_midpoint', .75)
        self.pixel_midpoint = config.getfloat('pixel_midpoint', 1)

        self.ratio_k = config.getfloat('ratio_k', 15)
        self.views_k = config.getfloat('views_k', 15)
        self.pixel_k = config.getfloat('pixel_k', 15)

        self.max_pages = config.getint('max_pages', 5)
        self.url = config.get('url', "https://api.imgur.com/3/gallery/r/{0}/top/all/{1}")
        self.album_url = config.get('album_url', "https://api.imgur.com/3/album/{0}")

        # imgur downloading
        self.client_id = config.get('client_id', "5f21952153b5f6c")
        self.headers = {"Authorization": "Client-ID {0}".format(self.client_id)}

        # where to store scored image metadata
        self.cache_file = os.path.expanduser(config.get('cache_file', '~/.cache/redrum_cache.json'))
        # where to store current_image
        self.image_file = os.path.expanduser(config.get('image_file', '~/.cache/redrum_image'))
        # how to set the background
        self.wallpaper_command = config.get('wallpaper_command', 'feh --bg-scale {image_file}')
        # set cache to expire after 1 week
        self.cache_expiry = timedelta(days=7)
        # use ctime format for storing cache date
        self.date_format = "%a %b %d %H:%M:%S %Y"
        # refresh cache when these options change
        self.options = [self.sfw_only, self.subreddits, self.screen_width, self.screen_height,
                        self.ratio_midpoint, self.views_midpoint, self.pixel_midpoint,
                        self.ratio_k, self.views_k, self.pixel_k, self.max_pages, self.url]

def main():

    parser = argparse.ArgumentParser(description="Reddit wallpaper grabber.")
    parser.add_argument('-v', '--version', action='version', version=__version__, help="show version information")
    parser.add_argument('--refresh', action='store_true', default=False, help="force a cache refresh")
    parser.add_argument('--noset', action='store_true', default=False, help="don't select and set and set wallpaper")
    parser.add_argument('--config', action='store_true', default='~/.config/redrum.ini', help="use a different config path")
    parser.add_argument('--debug', action='store_true', default=False, help="enable debug messages")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug('Debugging enabled...')

    config = Config(args.config)

    # attempt to load scored images from cache
    if not os.path.exists(config.cache_file):
        print("No previous score cache found at {0}.  This may take a minute...".format(config.cache_file))
        date = datetime.strftime(datetime.now(), config.date_format)
        images = get_images(config)
        seen = []

    else:
        with open(config.cache_file, 'r') as cache:
            j = json.loads(cache.read())
            print("Found cache at {0}".format(config.cache_file))
            date = j['date']
            # if the cache is old or `options` has changed, update it
            cache_age = datetime.now() - datetime.strptime(date, config.date_format)
            if (cache_age > config.cache_expiry or j['options'] != config.options or args.refresh):
                print("Refreshing cache...")
                # reload image metadata
                images = get_images(config)
                date = datetime.now().strftime(config.date_format)

            # otherwise, fetch scored images from cache
            else:
                images = j['images']

        seen = j['seen']

    # select image and set as wallpaper
    if not args.noset:
        image = weighted_select(config, images, seen)
        set_wallpaper(config, image)
        seen.append(image['id'])

    save(config, images, date, seen)

if __name__ == '__main__':
    main()
