#!/usr/bin/env python3
from dbus.exceptions import DBusException
import dbus
from time import sleep
import requests
import logging

INTERFACE = "org.mpris.MediaPlayer2.Player"
SPOTIFY_INTERFACE = "org.mpris.MediaPlayer2.spotify"
BLACKLIST_API_URL = "https:/ksg-nett-dev.samfundet.no"
LOG_PATH = "/var/log/soci-daemon.log"


PLAYER = None

bus = dbus.SessionBus()

def get_blacklist_from_API():
  logging.info("Getting blacklist from API")
  try:
    request = requests.get(BLACKLIST_API_URL)
    if request.status_code == 200:
      return request.json()
    return request
  except requests.exceptions.ConnectionError as e:
    logging.error(f"Could not connect to API: {e}")
    return None



def init_dbus():
    logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG)
    logging.info("Initializing dbus")
    try:
        obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        global PLAYER
        PLAYER = dbus.Interface(obj, dbus_interface=INTERFACE)
        logging.info("Initialized dbus")
        return True
    except DBusException:
        logging.error("Could not connect to spotify")
        return False

def get_playing_id():
    obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
    song_properties = props.GetAll(INTERFACE)
    song_id = song_properties['Metadata']['mpris:trackid'].split("/")[-1]
    return song_id



def main():
  logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG)
  logging.info("Starting daemon")
  init_dbus()

  while (not init_dbus()):
    sleep(5)

  blacklist = None
  while not blacklist:
    blacklist = get_blacklist_from_API()
    if not blacklist:
      logging.log("Could not retrieve blacklist from API. Sleeping for 5 seconds")
      sleep(5)
      continue

    init_dbus()

  while True:
    blacklist = get_blacklist_from_API()
    skip_check = get_playing_id() in blacklist
    if skip_check:
        logging.info(f"Skipping song {get_playing_id()}")
        PLAYER.Next()
        skip_check = False
        sleep(5)
    sleep(2)




if __name__ == "__main__":
  main()
