#!/usr/bin/env python 
from dbus.exceptions import DBusException
import dbus
from time import sleep
import requests

INTERFACE = "org.mpris.MediaPlayer2.Player"
SPOTIFY_INTERFACE = "org.mpris.MediaPlayer2.spotify"
BLACKLIST_API_URL = "https://ksg-nett.samfundet.no/api/blacklist"
PLAYER = None

def main():
  print("Starting daemon")
  init_dbus()

  while (not init_dbus()):
    sleep(5)

  blacklist = None
  print("Blaklist initialized")
  while not blacklist:
    request = get_blacklist_from_API()
    if not request:
      sleep(5)
      continue

    if request.status_code == 200:
      blacklist = request.json()
    else:
      print("Error: " + request.text)
      sleep(5)
      continue
  

  while True:
    skip_check = get_playing_id() in blacklist
    if skip_check:
        print("skipping")
        PLAYER.Next()
        skip_check = False
        sleep(5)




def get_blacklist_from_API():
  print(f"Retrieving blacklist from {BLACKLIST_API_URL}")
  try:
    request = requests.get(BLACKLIST_API_URL)
    return request
  except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
    return None



def init_dbus():
    try:
        obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")

        global PLAYER
        PLAYER = dbus.Interface(obj, dbus_interface=interface)
        return True
    except DBusException:
        print("Could not connect to Spotify! Is it running?")
        return False

def get_playing_id():
    obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
    song_properties = props.GetAll(interface)
    return song_properties['Metadata']['mpris:trackid']



if __name__ == "__main__":
  main()
