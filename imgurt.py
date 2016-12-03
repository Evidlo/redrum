#!/bin/env python3
## Evan Widloski - 2016-12-03
## Imgurt - Imgur wallpaper ranker and changer

import requests
import logging
import random
import math
from subprocess import Popen, PIPE

screen_width = 1600
screen_height = 900

subreddits = ["winterporn", "earthporn"]
url = "https://api.imgur.com/3/gallery/r/{0}/top/year/{1}"
album_url = "https://api.imgur.com/3/album/{0}"

# imgur api id
client_id = "5f21952153b5f6c"
headers = {"Authorization":"Client-ID {0}".format(client_id)}
# maximum number of pages of images to load for 1 subreddit
max_pages = 5

# Use logistic function to give better differeniation between good and bad matches.
# preset weights for scoring algorithm
#   see https://en.wikipedia.org/wiki/Logistic_function
#
#                                               weight -->  ‚------
#                       1                                  /
#   f(x) = ----------------------------       ------------/-------------
#          1 + e^(-k(score - midpoint))                  /
#                                                 ------‘ ∧    k = slope
#                                                         |
#                                                      midpoint
ratio_k = 10
views_k = 5
pixel_k = 5

ratio_midpoint = .95
views_midpoint = .75
pixel_midpoint = .75

ratio_weight = 3
views_weight = 1
pixel_weight = 3

import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)
# hide annoying requests messages
logging.getLogger("requests").setLevel(logging.WARNING)

# return a list of scores given a list of images
# lower score is better
def scores(images):
    scores = []
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

        scores.append(  1/(1 + pow(math.e, -ratio_k * (ratio_score - ratio_midpoint)))
                        * ratio_weight
                      + 1/(1 + pow(math.e, -views_k * (views_score - views_midpoint)))
                        * views_weight
                      + 1/(1 + pow(math.e, -pixel_k * (pixel_score - pixel_midpoint)))
                        * pixel_weight)

    return scores

# --- Get list of images and albums ---

# list containing mix of images and albums
results = []
# get results for each subreddit
for subreddit in subreddits:
    # keep getting results on each subreddit album until there are none left
    page_num = 0
    while True:
        page_url = url.format(subreddit, page_num)
        logging.debug("Downloading page #{0} from subreddit {1}".format(page_num, subreddit))
        response = requests.get(page_url, headers=headers)
        page_results = response.json()['data']
        page_num += 1

        if len(page_results) == 0 or page_num > max_pages - 1:
            break
        else:
            results += page_results

    if page_num == 0:
        logging.info("No results found for subreddit {0}.".format(subreddit))

# --- Cleanup list of images and albums ---

# build list of images, replacing albums with images they contain
images = []
for result in results:
    # if result is an album, append its images
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

# --- Score images and select randomly by score ---

if len(images) > 0:
    image_scores = scores(images)
else:
    logging.info("No results found")

#select a random image weighted by score
rand_score = random.uniform(0, sum(image_scores))
for image_score in image_scores:
    rand_score -= image_score
    if rand_score <= 0:
        image = images[image_scores.index(image_score)]
        break

# --- Set wallpaper with feh ---

logging.info("Selected {0} with probability {1}".format(image['link'], image_score/sum(image_scores)))
logging.info("Applying wallpaper")
response = requests.get(image['link'], headers=headers)
p = Popen(['feh', '-', '--bg-fill'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
logger.debug("feh response: {0}".format(p.communicate(input=(response.content))))
