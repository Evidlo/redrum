#!/bin/env python3
## Evan Widloski - Tuning Script for Imgurt
## Check scores for images of various ratios, resolutions, views
## Shows individual scores before and after logistic discrimination

## Look at columns 2-4 to make adjustments to ranking parameters
## For example, if an image with poor aspect ratio has a ratio score of .4
##   but a good image has a ratio score of .8, consider setting
##   ratio_cutoff to something between these two numbers.

from imgurt import *

# put some images of varying quality here to see their score before and after logistic function
# these images must be selected from imgurt_cache
links = ['D331RXf', # bad aspect ratio and resolution, high views
         'P7I7bML', # good aspect ratio and resolution
         'GW2i3K4', # good ratio and resolution, low views
         ]


f = open(cache_file, 'r')
j = json.loads(f.read())
images = j['images']

max_views = max([image['views'] for image in images])

print("%-12s  |  %-12s%-12s%-7s  |  %-12s%-12s%-7s  |  %-12s" % ("ID", "ratio", "views", "pixel", "ratio_l", "views_l", "pixel_l", "final"))
print("=======================================================================================================")
for link in links:
    image = [image for image in images if image['id'] == link][0]

    [final_score,
     ratio_score,
     views_score,
     pixel_score,
     ratio_logistic_score,
     views_logistic_score,
     pixel_logistic_score] = score_image(image, max_views)


    print("%-12s  |  %-12.5f%-12.5f%-7.5f  |  %-12.5f%-12.5f%-7.5f  |  %-12.11f" % (image['id'],
                                                                              ratio_score,
                                                                              views_score,
                                                                              pixel_score,
                                                                              ratio_logistic_score,
                                                                              views_logistic_score,
                                                                              pixel_logistic_score,
                                                                              final_score))

    print("-------------------------------------------------------------------------------------------------------")
