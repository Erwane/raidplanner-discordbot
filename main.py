# -*- coding: utf-8 -*-

import discord
import json
import locale
import src as bot

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

with open('config/config.json', 'r') as f:
    config = json.load(f)

client = discord.Client()
Bot = bot.Bot(client)

if __name__ == '__main__':
    Bot.run(config['token'])
    # client.run(config['token'])
