# -*- coding: utf-8 -*-

import os, json, locale
import src as bot
from src.mylibs import log

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
rootPath = os.path.dirname(os.path.realpath(__file__))
config = {}
with open(rootPath + '/config/config.json', 'r') as f:
    config = json.load(f)
config['rootPath'] = rootPath
Bot = bot.Bot(config)
# Bot.run()


# Api = bot.Api({'api': {
#     'base_url': 'http://192.168.33.1:3000',
#     'key': "myTestKey",
#     'secret': 'MySecretTestKey'
#     }
# })

# # response = Api.nextEvents()
# response = Api.setPresence(9649, 1, 'maybe', 519451096951947264)

