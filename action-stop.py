#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import paho.mqtt.client as paho
import paho.mqtt.publish as publish
import time
import json
import pytoml
import random
import os

#time.sleep(1)

SNIPS_CONFIG_PATH = '/etc/snips.toml'
siteId = 'default'
mqttServer = '127.0.0.1'
mqttPort = 1883

ACK = [u"Très bien", "OK", "daccord", u"C'est fait", u"Pas de problème", "entendu"]
STOP_WORDS = [
    u"stop ça",
    u"arrête ça",
    u"arrête la musique",
    u"stop la musique",
    u"stoppe la musique",
    u"quitte",
    u"quitte tout",
    u"quitter",
    u"arrête",
    u"arrête tout",
    u"stop tout",
    u"stoppe tout",
    u"stoppe",
    u"stop"
]

def pickAckWord():
    return ACK[random.randint(0, len(ACK) - 1)]

def loadConfigs():
	global mqttServer, mqttPort, siteId, hotwordId

	if os.path.isfile(SNIPS_CONFIG_PATH):
		with open(SNIPS_CONFIG_PATH) as confFile:
			configs = pytoml.load(confFile)
			if 'mqtt' in configs['snips-common']:
				if ':' in configs['snips-common']['mqtt']:
					mqttServer = configs['snips-common']['mqtt'].split(':')[0]
					mqttPort = int(configs['snips-common']['mqtt'].split(':')[1])
				elif '@' in configs['snips-common']['mqtt']:
					mqttServer = configs['snips-common']['mqtt'].split('@')[0]
					mqttPort = int(configs['snips-common']['mqtt'].split('@')[1])
			if 'bind' in configs['snips-audio-server']:
				if ':' in configs['snips-audio-server']['bind']:
					siteId = configs['snips-audio-server']['bind'].split(':')[0]
				elif '@' in configs['snips-audio-server']['bind']:
					siteId = configs['snips-audio-server']['bind'].split('@')[0]
			if 'hotword_id' in configs['snips-hotword']:
				hotwordId = configs['snips-hotword']['hotword_id']
	else:
		print('Snips configs not found')


def on_message(client, userdata, message):
    topic = message.topic
    msg=str(message.payload.decode("utf-8","ignore"))
    msgJson=json.loads(msg)

    print "[Topic]: " + str(topic)
    print "[Payload]: " + msg


    if topic == "hermes/hotword/default/detected":
        if msgJson["modelId"] == "stop":
            publish.single('hermes/artifice/stop', payload=json.dumps({'siteId': msgJson["siteId"]}), hostname=mqttServer, port=mqttPort)
    elif "text" in msgJson and msgJson["text"].lower() in STOP_WORDS:
        global mqttServer, mqttPort, siteId
        publish.single('hermes/dialogueManager/endSession', payload=json.dumps({'sessionId': msgJson["sessionId"], 'text': pickAckWord()}), hostname=mqttServer, port=mqttPort)

def on_connect(client, userdata, flag, rc):
    print("connected")
    print(rc)

def on_disconnected(client, userdata, rc):
    print("disconnected")

def on_log(client, userdata, level, buf):
    print("log: ",buf)

loadConfigs()
tmpClient = paho.Client("action-stop-"+siteId)
tmpClient.on_message=on_message
tmpClient.on_connect=on_connect
tmpClient.on_log=on_log
tmpClient.connect(mqttServer, mqttPort)
tmpClient.subscribe("hermes/asr/textCaptured")
tmpClient.subscribe("hermes/hotword/default/detected") #python script-recording.py stop
# tmpClient.subscribe("hermes/asr/partialTextCaptured")
tmpClient.loop_forever()