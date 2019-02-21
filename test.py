# -*- coding: utf-8 -*-

import src as bot
from src.mylibs import log

log().debug(f"Api::get - url=/aze; headers=azeaz")
log().info(f"Api::get - url=/aze; headers=azeaz")
log().warning(f"Api::get - url=/aze; headers=azeaz")
log().critical(f"Api::get - url=/aze; headers=azeaz")

# Api = bot.Api({'api': {
#     'base_url': 'http://192.168.33.1:3000',
#     'key': "myTestKey",
#     'secret': 'MySecretTestKey'
#     }
# })

# # response = Api.nextEvents()
# response = Api.setPresence(9649, 1, 'maybe', 519451096951947264)

