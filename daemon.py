#!/usr/bin/env python
from dbus.exceptions import DBusException
import dbus
from time import sleep
import requests

INTERFACE = "org.mpris.MediaPlayer2.Player"
SPOTIFY_INTERFACE = "org.mpris.MediaPlayer2.spotify"
BLACKLIST_API_URL = "http://localhost:8000/api/blacklist"

PLAYER = None

bus = dbus.SessionBus()

def main():
  print("Starting daemon")
  init_dbus()

  while (not init_dbus()):
    sleep(5)

  blacklist = None
  print("Blaklist initialized")
  while not blacklist:
    blacklist = get_blacklist_from_API()
    if not blacklist:
      sleep(5)
      print("No response trying again in 5")
      continue

  

    init_dbus()

  while True:
    blacklist = get_blacklist_from_API()
    skip_check = get_playing_id() in blacklist
    if skip_check:
        print("skipping")
        print(PLAYER)
        PLAYER.Next()
        skip_check = False
    sleep(5)




def get_blacklist_from_API():
  print(f"Retrieving blacklist from {BLACKLIST_API_URL}")
  try:
    request = requests.get(BLACKLIST_API_URL)
    if request.status_code == 200:
      return request.json()
    return request
  except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
    return None



def init_dbus():
    try:
        obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        print(obj)

        global PLAYER
        PLAYER = dbus.Interface(obj, dbus_interface=INTERFACE)
        return True
    except DBusException:
        print("Could not connect to Spotify! Is it running?")
        return False

def get_playing_id():
    obj = bus.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
    props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
    song_properties = props.GetAll(INTERFACE)
    #split on / and get last element
    print(song_properties)
    song_id = song_properties['Metadata']['mpris:trackid'].split("/")[-1]
    return song_id



if __name__ == "__main__":
  main()
