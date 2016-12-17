#!/bin/env python3
## Evan Widloski - Tuning Script for Imgurt
## Check scores for images of various ratios, resolutions, views
from imgurt import *

links = ['http://i.imgur.com/D331RXf.jpg', # an image with bad aspect ratio, resolution
         'http://i.imgur.com/P7I7bML.jpg'] # good aspect ratio, resolution


f = open(cache_file, 'r')
j = json.loads(f.read())
images = j['images']

max_views = max([image['views'] for image in images])

print("%-12s%-12s%-12s%-12s%-12s%-12s%-12s%-12s" % ("ID", "ratio", "views", "pixel", "ratio_l", "views_l", "pixel_l", "final"))
print("==============================================================================================")
for link in links:
    image = [image for image in images if image['link'] == link][0]

    final_score = score_image(image, max_views)

    import pdb
    pdb.set_trace()
    print("%12s%12.5f%12.5f%12.5f  |  %.5f%12.5f%12.5f | %.5f" % (image['id'],
                                                                  score_image.ratio_score,
                                                                  score_image.views_score,
                                                                  score_image.pixel_score,
                                                                  score_image.ratio_logistic_score,
                                                                  score_image.views_logistic_score,
                                                                  score_image.pixel_logistic_score,
                                                                  final_score), end="")

    print("%15.10f" % (ratio_score * views_score * pixel_score))
    print("----------------------------------------------------------------------------------------------")
