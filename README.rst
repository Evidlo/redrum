Redrum - Reddit Wallpaper Downloader and Ranker
==============================================

.. image:: screenshot.png

Redrum is a Reddit wallpaper downloader which scores wallpapers and selects the best based on resolution, aspect ratio, and number of views.  It remembers which wallpapers were selected previously so you never see the same image twice.

Install the systemd units to run the script every two hours.

Installation
------------

1. Install through pip

   .. code:: bash

      pip3 install redrum
  
2. Install systemd user unit (optional)

   * edit `systemd/redrum.service` to point to `redrum.py`

   * copy unit files

   .. code:: bash

      # copy service files
      cp -u systemd/* ~/.config/systemd/user/

      # enable and start systemd timer
      systemctl --user enable redrum.timer
      systemctl --user start redrum.timer

      # the service can be triggered manually as well
      systemctl --user start redrum
  
Usage
-----

If redrum can't find a config file, it will create one in `~/.config/redrum.ini` automatically.  You should update this file with your screen resolution and preferred subreddits, then run redrum again.

.. code:: bash

   >>> redrum
   No config found at /home/evan/.config/redrum.ini.  Creating...
   Update config with your preferred options and run redrum again.

   >>> redrum
   No previous score cache found at /home/evan/.cache/redrum_cache.json.
   Indexing page #0 from subreddit winterporn
   Indexing page #1 from subreddit winterporn
   Indexing page #2 from subreddit winterporn
   ...
   Selected http://i.imgur.com/3UWbcYG.jpg (EarthPorn) with score 5.21729920261845e-05 out of 5971 images
   The probability of selecting this image was 0.009851421028579594
   Applying wallpaper

  
  
