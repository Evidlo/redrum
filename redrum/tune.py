#!/bin/env python3
## Evan Widloski - 2017-05-01 - Graphical Tuning Script for redrum
## Check scores for images of various ratios, resolutions, views
## Shows individual scores before and after logistic discrimination
## Note: Images tested in tune.py must be in the redrum cache

## examples:
##   tune.py D331RXf P7I7bML DX352lK # compare scores for three images
##   tune.py --ratio_midpoint .8 D331RXf P7I7bML DX352lK # override ratio_midpoint

import argparse
import redrum
import json

# read in parameter overrides
parser = argparse.ArgumentParser()
parser.add_argument('--ratio_midpoint', type=float)
parser.add_argument('--ratio_k', type=float)
parser.add_argument('--pixel_midpoint', type=float)
parser.add_argument('--pixel_k', type=float)
parser.add_argument('--views_midpoint', type=float)
parser.add_argument('--views_k', type=float)
parser.add_argument('ids', metavar='imgur_id', type=str, nargs='+', help="image ID to score from the cache")

args = parser.parse_args()
if args.ratio_midpoint:
    redrum.ratio_midpoint = args.ratio_midpoint
if args.ratio_k:
    redrum.ratio_k = args.ratio_k
if args.pixel_midpoint:
    redrum.pixel_midpoint = args.pixel_midpoint
if args.pixel_k:
    redrum.pixel_k = args.pixel_k
if args.views_midpoint:
    redrum.views_midpoint = args.views_midpoint
if args.views_k:
    redrum.views_k = args.views_k
if args.ids:
    ids = args.ids

# load images in the cache
f = open(redrum.cache_file, 'r')
j = json.loads(f.read())
images = j['images']

max_views = max([image['views'] for image in images])

# print scores in a tabular format
print("{:^60} {:<31}".format("Input Scores", "Logistic Scores"))
print("%-12s  |  %-12s%-12s%-7s  |  %-12s%-12s%-7s  |  %-12s" % ("ID", "ratio", "views", "pixel", "ratio", "views", "pixel", "final_score"))
print("=" * 103)
# calculate and print scores and logistic scores for each image
for id in ids:
    image = [image for image in images if image['id'] == id][0]

    [final_score,
     ratio_score,
     views_score,
     pixel_score,
     ratio_logistic_score,
     views_logistic_score,
     pixel_logistic_score] = redrum.score_image(image, max_views)


    print("%-12s  |  %-12.5f%-12.5f%-7.5f  |  %-12.5f%-12.5f%-7.5f  |  %-12.11f" % (image['id'],
                                                                              ratio_score,
                                                                              views_score,
                                                                              pixel_score,
                                                                              ratio_logistic_score,
                                                                              views_logistic_score,
                                                                              pixel_logistic_score,
                                                                              final_score))

    print("-" * 103)
