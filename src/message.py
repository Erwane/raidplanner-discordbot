# -*- coding: utf-8 -*-

import asyncio
import discord
import re
from .setup import Setup

class Message:
    def __init__(self, client, db, api):
        self.api = api
        self.client = client
        self.db = db

    async def on(self, message):
        # ignore myself
        if message.author == self.client.user:
            return

        command = re.match("^!rp ([^ ]+)( ?)(.*)", message.content.lower())

        # only my commands
        if command != None:
            # print(f"command '{command.group(1)}' by {message.author.id} in {message.channel.id} of {message.guild.id}")
            try:
                await getattr(self, '_%s' % command.group(1))(message)
            except Exception as e:
                return

    async def _help(self, msg):
        myEmbed = discord.Embed(title="Raidplanner help", description="Aide pour le bot Raidplanner", colour=0xff0000)
        try:
            await msg.author.send("this is my help", embed=myEmbed)
        except Exception as e:
            raise e

    async def _me(self, msg):
        print(f"me: {msg.author.id}")

    async def _attach(self, msg):
        setup = Setup(self.client, self.db, self.api)

        await setup.attach(msg)
