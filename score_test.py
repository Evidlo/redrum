#!/bin/env python3
## Evan Widloski - Tuning Script for Imgur
## Check scores for images of various ratios, resolutions, views
from imgurt import *

links = ['http://i.imgur.com/D331RXf.jpg', # an image with bad aspect ratio, resolution
         'http://i.imgur.com/P7I7bML.jpg'] # good aspect ratio, resolution


f = open(cache_file, 'r')
j = json.loads(f.read())
images = j['images']

max_views = max([image['views'] for image in images])

print("ID        ratio       views       pixel         ratio_l     views_l     pixel_l   final     ")
print("==============================================================================================")
for link in links:
    image = [image for image in images if image['link'] == link][0]

    [ratio_score, views_score, pixel_score] = score_image(image, max_views)
    ratio_logistic_score = 1/(1 + pow(math.e, -ratio_k * (ratio_score - ratio_cutoff)))
    views_logistic_score = 1/(1 + pow(math.e, -views_k * (views_score - views_cutoff)))
    pixel_logistic_score = 1/(1 + pow(math.e, -pixel_k * (pixel_score - pixel_cutoff)))

    print(image['id'], end="")
    print("%10.5f  %10.5f  %10.5f" % (ratio_score, views_score, pixel_score), end="   |")
    print("%10.5f  %10.5f  %10.5f" % (ratio_logistic_score,
                                      views_logistic_score,
                                      pixel_logistic_score), end="")
    print("%15.10f" % (ratio_score * views_score * pixel_score))
    print("----------------------------------------------------------------------------------------------")
