# -*- coding: utf-8 -*-

import src as bot

Api = bot.Api({'api': {
    'base_url': 'http://192.168.33.1:3000',
    'key': "myTestKey",
    'secret': 'MySecretTestKey'
    }
})

response = Api.nextEvents()
# response = Api.setPresence(9648, 1, 'maybe')

print(response)
