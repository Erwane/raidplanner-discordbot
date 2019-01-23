# -*- coding: utf-8 -*-

class Reaction:
    def __init__(self, api, discordClient):
        self.api = api
        self.client = discordClient
        self.no = "🚫"
        self.yes = "✅"
        self.maybe = "❓"

    # 308664314993180673 react on 535753694982176789 with reaction: ✅
    async def on(self, payload):
        # ignore myself
        if payload.user_id == self.client.user.id:
            return

