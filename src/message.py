# -*- coding: utf-8 -*-

import re

class Message:
    def __init__(self, discordClient):
        self.client = discordClient

    def _getApi(self):
        api = api()

        api

    async def on(self, message):
        # ignore myself
        if message.author == self.client.user:
            return

        command = re.match("^!rp ([^ ]+)( ?)(.*)", message.content.lower())

        # only my commands
        if command == None:
            return
        else:
            # print(f"command '{command.group(1)}' by {message.author.id} in {message.channel.id} of {message.guild.id}")
            try:
                await getattr(self, '_%s' % command.group(1))(message)
            except Exception as e:
                return

        if "rpbot.close" == message.content.lower():
            print(f"closing client ...")
            await message.channel.send("Bye!!")
            await self.client.close()

    async def _me(self, msg):
        print(f"me: {msg.author.id}")
