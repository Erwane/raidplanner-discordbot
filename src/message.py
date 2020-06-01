# -*- coding: utf-8 -*-

import asyncio
import discord
import re
from .setup import Setup
from pprint import pprint

class Message:
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db

    async def on(self, message):
        prefix = await self.bot.client.get_prefix(message)
        pprint(prefix)
        pprint(message)

        # if (!message.content.startsWith("!rp") || message.author.bot) return;

        # args = message.content.slice(prefix.length).split(' ');

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
                name="!rp status",
                value="""Affiche le statut du robot pour ce serveur.""",
                inline=False
            ).add_field(
                name="!rp detach",
                value="""Détache le robot de votre guilde MMOrga. Il ne plubliera plus d'événement.""",
                inline=False
            ).add_field(
                name="!rp chan",
                value="""Définit le canal où seront publiés les événements. Les droits nécessaires sont disponibles dans la documentation.""",
                inline=False
            ).add_field(
                name="!rp days",
                value="""Les événements ayant lieu dans les `x` jours seront publiés dans le canal. Par défaut **7**""",
                inline=False
            ).add_field(
                name="Documentation",
                value="""Retrouvez toute la documentation sur cette page : https://mmorga.org/content/discord""",
                inline=True
            )

            await msg.author.send("", embed=myEmbed)
        except Exception as e:
            raise e
