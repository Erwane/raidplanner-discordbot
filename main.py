# -*- coding: utf-8 -*-

import locale
import src as bot

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

Bot = bot.Bot()
if __name__ == '__main__':
    Bot.run()
