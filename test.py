# -*- coding: utf-8 -*-

import os, json, locale, sqlite3, time
import src as bot
from src.mylibs import log
from pprint import pprint

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
rootPath = os.path.dirname(os.path.realpath(__file__))
config = {}
with open(rootPath + '/config/config.json', 'r') as f:
    config = json.load(f)
config['rootPath'] = rootPath
Bot = bot.Bot(config)
# Bot.run()

user = Bot.db.getUser(165076810651009024)

pprint(dict(user))


# Api = bot.Api({'api': {
#     'base_url': 'http://192.168.33.1:3000',
#     'key': "myTestKey",
#     'secret': 'MySecretTestKey'
#     }
# })

# # response = Api.nextEvents()
# response = Api.setPresence(9649, 1, 'maybe', 519451096951947264)

