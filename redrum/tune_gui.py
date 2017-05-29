#!/bin/python
# Evan Widloski - 2016-10-13
# Visually demonstrate f(z) = e^z
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import redrum
import math
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('ids', metavar='imgur_id', type=str, nargs='+', help="image ID to score from the cache")
args = parser.parse_args()

fig, ax = plt.subplots(figsize=(15,5))
plt.subplots_adjust(left=0.05, bottom=0.3, right=.95)

x = np.arange( 0, 1, 0.001)


#-------------- Inputs -----------------

axis_color = 'lightgoldenrodyellow'
slide_ratio_midpoint_axis = plt.axes([0.05,  0.1, 0.15, 0.03], axisbg=axis_color)
slide_ratio_k_axis =        plt.axes([0.05, 0.15, 0.15, 0.03], axisbg=axis_color)
slide_pixel_midpoint_axis = plt.axes([0.29,  0.1, 0.15, 0.03], axisbg=axis_color)
slide_pixel_k_axis =        plt.axes([0.29, 0.15, 0.15, 0.03], axisbg=axis_color)
slide_views_midpoint_axis = plt.axes([0.52,  0.1, 0.15, 0.03], axisbg=axis_color)
slide_views_k_axis =        plt.axes([0.52, 0.15, 0.15, 0.03], axisbg=axis_color)

slide_ratio_midpoint = Slider(slide_ratio_midpoint_axis, 'midpoint', 0, 1, valinit=redrum.ratio_midpoint)
slide_ratio_k = Slider(slide_ratio_k_axis, 'k', 0, 40, valinit=redrum.ratio_k)
slide_pixel_midpoint = Slider(slide_pixel_midpoint_axis, 'midpoint', 0, 1, valinit=redrum.pixel_midpoint)
slide_pixel_k = Slider(slide_pixel_k_axis, 'k', 0, 40, valinit=redrum.pixel_k)
slide_views_midpoint = Slider(slide_views_midpoint_axis, 'midpoint', 0, 1, valinit=redrum.views_midpoint)
slide_views_k = Slider(slide_views_k_axis, 'k', 0, 40, valinit=redrum.views_k)

#-------------- Plots -----------------
ax.hold()

# just create plots with zeroed data for now.  the plots will be updated with data later
plot_ratio_axis = plt.subplot(1,4,1)
plot_ratio, = plt.plot(0, 1, lw=2, color='gray')
plt.title('Ratio')
plt.axis([0, 1, 1 / math.e, 1])
plot_ratio_score_a, = plot_ratio_axis.plot(0, 0, 'ro')
plot_ratio_score_b, = plot_ratio_axis.plot(0, 0, 'bo')
ratio_score_ratio_text = plot_ratio_axis.text(.05, .95, '')

plot_pixel_axis = plt.subplot(1,4,2)
plt.title('Pixel')
plot_pixel, = plt.plot(0, 0, lw=2, color='gray')
plt.axis([0, 1, 1 / math.e, 1])
plot_pixel_score_a, = plot_pixel_axis.plot(0, 0, 'ro')
plot_pixel_score_b, = plot_pixel_axis.plot(0, 0, 'bo')
pixel_score_ratio_text = plot_pixel_axis.text(.05, .95, '')

plot_views_axis = plt.subplot(1,4,3)
plt.title('Views')
plot_views, = plt.plot(0, 0, lw=2, color='gray')
plt.axis([0, 1, 1 / math.e, 1])
plot_views_score_a, = plot_views_axis.plot(0, 0, 'ro')
plot_views_score_b, = plot_views_axis.plot(0, 0, 'bo')
views_score_ratio_text = plot_views_axis.text(.05, .95, '')

plot_final_score_axis = plt.subplot(1,4,4)
plt.title('Final Score')
bbox_a = dict(boxstyle='round', facecolor='red', alpha=0.2)
bbox_b = dict(boxstyle='round', facecolor='blue', alpha=0.2)
plot_final_score_axis.axis('off')
final_score_a_text = plot_final_score_axis.text(.05, .85, '', bbox=bbox_a)
final_score_b_text = plot_final_score_axis.text(.05, .75, '', bbox=bbox_b)
final_score_ratio_text = plot_final_score_axis.text(.05, .65, '')

plot_ratio.set_xdata(x)
plot_pixel.set_xdata(x)
plot_views.set_xdata(x)

#-------------- Load Images -----------------

f = open(redrum.cache_file, 'r')
j = json.loads(f.read())
images = j['images']
max_views = max([image['views'] for image in images])
image_a = [image for image in images if image['id'] == args.ids[0]][0]
if not image_a:
    raise('Image ID {} not found in cache.'.format(args.ids[0]))
image_b = [image for image in images if image['id'] == args.ids[1]][0]
if not image_b:
    raise('Image ID {} not found in cache.'.format(args.ids[1]))

#-------------- Make plots interactive -----------------

# update plots and scores when sliders are adjusted
def update(*_):
    redrum.ratio_midpoint = slide_ratio_midpoint.val
    redrum.ratio_k = slide_ratio_k.val
    redrum.pixel_midpoint = slide_pixel_midpoint.val
    redrum.pixel_k = slide_pixel_k.val
    redrum.views_midpoint = slide_views_midpoint.val
    redrum.views_k = slide_views_k.val
    plot_ratio.set_ydata(redrum.logistic_function(x, slide_ratio_midpoint.val, slide_ratio_k.val))
    plot_pixel.set_ydata(redrum.logistic_function(x, slide_pixel_midpoint.val, slide_pixel_k.val))
    plot_views.set_ydata(redrum.logistic_function(x, slide_views_midpoint.val, slide_views_k.val))
    [final_score_a,
     ratio_score_a,
     views_score_a,
     pixel_score_a,
     ratio_logistic_score_a,
     views_logistic_score_a,
     pixel_logistic_score_a] = redrum.score_image(image_a, max_views)
    [final_score_b,
     ratio_score_b,
     views_score_b,
     pixel_score_b,
     ratio_logistic_score_b,
     views_logistic_score_b,
     pixel_logistic_score_b] = redrum.score_image(image_b, max_views)
    plot_ratio_score_a.set_xdata(ratio_score_a)
    plot_ratio_score_a.set_ydata(ratio_logistic_score_a)
    plot_ratio_score_b.set_xdata(ratio_score_b)
    plot_ratio_score_b.set_ydata(ratio_logistic_score_b)
    ratio_score_ratio_text.set_text('rel. prob. = {:.2e}'.format(ratio_logistic_score_a / ratio_logistic_score_b))

    plot_pixel_score_a.set_xdata(pixel_score_a)
    plot_pixel_score_a.set_ydata(pixel_logistic_score_a)
    plot_pixel_score_b.set_xdata(pixel_score_b)
    plot_pixel_score_b.set_ydata(pixel_logistic_score_b)
    pixel_score_ratio_text.set_text('rel. prob. = {:.2e}'.format(pixel_logistic_score_a / pixel_logistic_score_b))

    plot_views_score_a.set_xdata(views_score_a)
    plot_views_score_a.set_ydata(views_logistic_score_a)
    plot_views_score_b.set_xdata(views_score_b)
    plot_views_score_b.set_ydata(views_logistic_score_b)
    views_score_ratio_text.set_text('rel. prob. = {:.2e}'.format(views_logistic_score_a / views_logistic_score_b))

    final_score_a_text.set_text('{} score = {:.2e}'.format(args.ids[0], final_score_a))
    final_score_b_text.set_text('{} score = {:.2e}'.format(args.ids[1], final_score_b))
    final_score_ratio_text.set_text('rel. prob. = {:.2e}'.format(final_score_a / final_score_b))
    fig.canvas.draw_idle()

slide_ratio_midpoint.on_changed(update)
slide_ratio_k.on_changed(update)
slide_pixel_midpoint.on_changed(update)
slide_pixel_k.on_changed(update)
slide_views_midpoint.on_changed(update)
slide_views_k.on_changed(update)

reset_axes = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(reset_axes, 'Reset', color=axis_color, hovercolor='0.975')


# reset slider values
def reset(event):
    slide_ratio_midpoint.reset()
    slide_ratio_k.reset()
    slide_pixel_midpoint.reset()
    slide_pixel_k.reset()
    slide_views_midpoint.reset()
    slide_views_k.reset()
button.on_clicked(reset)

# initialize plots, pass 
update()

plt.show()
