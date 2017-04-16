Imgurt - Imgur Wallpaper Downloader and Ranker
==============================================

.. image:: screenshot.png

Imgurt is a wallpaper downloader which scores wallpapers and selects the best based on resolution, aspect ratio, and number of views.  It remembers which wallpapers were selected previously so you  never see the same image twice.

Install the systemd units to run the script every two hours.

Installation
------------

1. Install through pip

   .. code:: bash

      pip3 install imgurt
  
2. Install systemd user unit (optional)

   * edit `systemd/imgurt.service` to point to `imgurt.py`

   * copy unit files

   .. code:: bash

      # copy service files
      cp -u systemd/* ~/.config/systemd/user/

      # enable and start systemd timer
      systemctl --user enable imgurt.timer
      systemctl --user start imgurt.timer

      # the service can be triggered manually as well
      systemctl --user start imgurt
  
Usage
-----

If imgurt can't find a config file, it will create one in `~/.config/imgurt.ini` automatically.  You should update this file with your screen resolution and preferred subreddits, then run imgurt again.

.. code:: bash

   >>> imgurt
   No config found at /home/evan/.config/imgurt.ini.  Creating...
   Update config with your preferred options and run imgurt again.

  >>> imgurt
  No previous score cache found at /home/evan/.cache/imgurt_cache.json.
  Indexing page #0 from subreddit winterporn
  Indexing page #1 from subreddit winterporn
  Indexing page #2 from subreddit winterporn
  ...

  
  
