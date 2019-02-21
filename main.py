# -*- coding: utf-8 -*-

import json
import locale
import src as bot

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

config = {}
with open('config/config.json', 'r') as f:
    config = json.load(f)

Bot = bot.Bot(config)
if __name__ == '__main__':
    Bot.run()
