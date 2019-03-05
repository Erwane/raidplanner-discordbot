# -*- coding: utf-8 -*-

import asyncio
import discord
import re
from .setup import Setup

class Message:
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db

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
        try:
            myEmbed=discord.Embed(
                title="RaidplannerBot",
                url="https://mmorga.org/content/discord",
                description="""Ce robot permet aux membres de votre discord de définir leur présence aux événements que vous avez créés sur le site MMOrga/Raidplanner""",
                color=0x93765d
            ).set_thumbnail(
                url="https://cdn.discordapp.com/avatars/367796880824074240/01b803f15658f89ce22658cdf8c3b977.png?size=256"
            ).add_field(
                name="!rp attach",
                value="""Permet d'attacher le robot à votre guilde MMOrga. Vous trouverez votre token de guilde via la page https://mmorga.org/guild/my puis "options et robot discord".""",
                inline=False
            ).add_field(
                name="!rp detach",
                value="""Détache le robot de votre guilde MMOrga. Il ne plubliera plus d'événement.""",
                inline=False
            ).add_field(
                name="!rp chan",
                value="""Définit le canal où seront publiés les événements.""",
                inline=False
            ).add_field(
                name="Documentation",
                value="""Retrouvez toute la documentation sur cette page : https://mmorga.org/content/discord""",
                inline=True
            )

            await msg.author.send("", embed=myEmbed)
        except Exception as e:
            raise e

    async def _me(self, msg):
        print(f"me: {msg.author.id}")

    async def _attach(self, msg):
        setup = Setup(self.bot)
        await setup.attach(msg)

    async def _detach(self, msg):
        setup = Setup(self.bot)
        await setup.detach(msg)

    async def _chan(self, msg):
        setup = Setup(self.bot)
        await setup.chan(msg)
