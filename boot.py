# boot.py -- run on boot-up
import senko
import machine
import wifimgr
import WiFimgr_main

#connect_wifi()
wifimgr
WiFimgr_main

OTA = senko.Senko(
  user="oehlt2", # Required
  repo="BTW2402", # Required
  branch="master", # Optional: Defaults to "master"
  working_dir="nixie_clock", # Optional: Defaults to "app"
  files = ["main.py","ntp_servers.json"]
)

#This setup will try to updated all your predefined files every time microcontroller boots. 
if OTA.update():
    print("Updated to the latest version! Rebooting...")
    machine.reset()
