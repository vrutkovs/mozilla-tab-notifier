import os.path
import io
import json
import pathlib as p
import lz4.block as lz4
import paho.mqtt.client as mqtt
import logging
import time

# Const

MEETING_URLS=[
  'https://meet.google.com',
  'https://bluejeans.com'
]

# Register a binary sensor at Home Assistant
DEVICE='meeting_active'
TOPIC=f'finn/{DEVICE}'
BOOL2MQTT={True: "ON", False: "OFF"}

def on_log(client, userdata, level, buff):
    #otherwise we have silent exceptions
    logging.log(level, f"{userdata}-{buff}")

# Prepare session backup file path
PROFILE_DIR='/var/home/vrutkovs/.var/app/org.mozilla.firefox/.mozilla/firefox/4dwb0vhd.default-beta'
sessionBackupPath='sessionstore-backups/recovery.jsonlz4'
filePath=os.path.join(PROFILE_DIR, sessionBackupPath)

# Read file and find meeting urls, return True if meeting tab is open
def is_meeting_active():
    with io.open(filePath, "rb") as fd:
        fd.read(8)  # b"mozLz40\0"
        jdata = json.loads(lz4.decompress(fd.read()).decode("utf-8"))
        for win in jdata.get("windows"):
            for tab in win.get("tabs"):
                if not "index" in tab:
                    continue
                i = tab["index"] - 1
                url = tab["entries"][i]["url"]
                if any(url.startswith(meeting) for meeting in MEETING_URLS):
                    return True
    return False


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(levelname)s:%(message)s', level=logging.DEBUG)
    client = mqtt.Client()
    client.on_log = on_log
    client.username_pw_set(username=os.getenv("MQTT_USER"),password=os.getenv("MQTT_PASSWORD"))
    client.connect(os.getenv("MQTT_HOST"), 1883, 60)

    logging.debug("Registering at Home Assistant")
    config_payload = {
        "~": TOPIC,
        "name": "Active meeting",
        "unique_id": DEVICE,
        "state_topic": "~/state",
    }
    client.publish(
        f"homeassistant/binary_sensor/{DEVICE}/config",
        payload=json.dumps(config_payload),
        qos=0, retain=False)

    payload = None
    while True:
        new_payload = BOOL2MQTT[is_meeting_active()]
        if new_payload != payload:
            logging.debug(f"Payload changed: {new_payload}")
            client.publish(
                f"{TOPIC}/state",
                payload=new_payload,
                qos=0, retain=False)
            payload = new_payload
        time.sleep(1)
