#!/usr/bin/env python3
from dbus.exceptions import DBusException
import dbus
from time import sleep
import requests
import logging
import evdev
import threading
import playsound as playsound

INTERFACE = "org.mpris.MediaPlayer2.Player"
SPOTIFY_INTERFACE = "org.mpris.MediaPlayer2.spotify"
BLACKLIST_API_URL = "https:/ksg-nett-dev.samfundet.no"
LOG_PATH = "/var/log/soci-daemon.log"

PLAYER = None

bus = dbus.SessionBus()

PLING_INPUT_DEVICE = None


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


def initiate_pling_thread():
    global PLING_INPUT_DEVICE
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]  # Needs to run with admin priv to see system devices, there is no other way
    for device in devices:
        if device.name.contains(
                "Arduino"):  # Sets the first Arduino as input device, please do not connect multiple Arduinos
            PLING_INPUT_DEVICE = device
            break
    if PLING_INPUT_DEVICE != None:
        logging.log(
            "Starting pling thread with device: {}, {}, {}".format(PLING_INPUT_DEVICE.path, PLING_INPUT_DEVICE.name,
                                                                   PLING_INPUT_DEVICE.phys))
        pling_thread = threading.Thread(target=pling_listener, args=PLING_INPUT_DEVICE)
        pling_thread.start()
    else:
        logging.log(level=40, msg="Did not find a pling input device, skipping initialization of pling thread")


def pling_listener(device):
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            if event.code == 42 and event.value == 1:  # Checks for code = left_shift and value = pressed down
                pling()


def pling():
    PLAYER.Pause()
    try:
        playsound('rocka_i_esken_kort.mp3')
    except:
        logging.error("Could not play Pling sound")
    PLAYER.Play()


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

    initiate_pling_thread()

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
