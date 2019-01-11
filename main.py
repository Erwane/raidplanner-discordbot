'''
Raidplanner bot starting
'''

import asyncio
import discord
import inspect
import json

with open('config/config.json', 'r') as f:
    config = json.load(f)

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print('------')

    async def on_message(self, message):
        channel = message.channel

        # don't respond to ourselves
        if message.author == self.user:
            return
        if message.content.startswith('!test'):
            await self.send_message(channel, 'Hello {}'.format(message.author.id))
        elif message.content.startswith('!bye'):
            await self.send_message(channel, 'A plus (si ça marche)')
            await self.leave_server(channel.server)


client = MyClient()
client.run(config['token'])
