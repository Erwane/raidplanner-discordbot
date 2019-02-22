# -*- coding: utf-8 -*-

import os, json, locale
import src as bot

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

rootPath = os.path.dirname(os.path.realpath(__file__))

config = {}
with open(rootPath + '/config/config.json', 'r') as f:
    config = json.load(f)

config['rootPath'] = rootPath

Bot = bot.Bot(config)
if __name__ == '__main__':
    Bot.run()
