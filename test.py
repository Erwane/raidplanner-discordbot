# -*- coding: utf-8 -*-

import src as bot

Api = bot.Api({'api': {
    'base_url': '192.168.33.1:3000',
    'key': "myTestKey",
    'secret': 'MySecretTestKey'
    }
})

response = Api.getUser(1)

print(response)
