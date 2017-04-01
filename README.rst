Imgurt - Imgur Wallpaper Downloader and Ranker
==============================================

Imgurt is a wallpaper downloader which scores wallpapers and selects the best based on resolution, aspect ratio, and number of views.  It remembers which wallpapers were selected previously so you  never see the same image twice.

Install the systemd units to run the script every two hours.

Usage
-----

.. code:: bash

   python3 imgurt.py

Installation
------------

1. Install dependencies

   .. code:: bash

      pip3 install requests
  
   Also install ``feh`` using your distribution's package manager.
  
2. Install systemd user unit (optional)

  * edit `systemd/imgurt.service` to point to `imgurt.py`

  * copy unit files

    .. code:: bash

       cp -u systemd/* ~/.config/systemd/user/
       systemctl --user enable imgurt.timer
       systemctl --user start imgurt.timer
  

  
  
