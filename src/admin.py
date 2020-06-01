# -*- coding: utf-8 -*-

import asyncio
import discord
from pprint import pprint

class Admin:
    def __init__(self, bot):
        self.bot = bot.client
        self.api = bot.api
        self.db = bot.db

    async def status(self, ctx, args):
        servers = self.bot.guilds
        guilds = self.db.fetchall("SELECT id FROM guilds")
        events = self.db.fetchall("SELECT id FROM events")

        message = (
            f"Serveurs connectés : {len(servers)}\n"
            f"Guilde liées : {len(guilds)}\n"
            f"Evénéments gérés : {len(events)}"
        )

        await ctx.author.send(message)

    async def sync_guilds(self, ctx, args):
        attachedGuilds = dict()
        rows = self.db.fetchall("SELECT id, rp_token, response FROM guilds")
        for row in rows:
            attachedGuilds[row['id']] = row

        botGuilds = dict()
        for guild in self.bot.guilds:
            botGuilds[guild.id] = guild

        logs = []

        for key, attached in attachedGuilds.items():
            if not attached['id'] in botGuilds:
                # Bot is attached but not on server
                self.api.discordDetach(ctx.author, False, attached)
                self.db.query('DELETE FROM events WHERE guild_id=?', attached['id'])
                # self.db.query('DELETE FROM guilds WHERE id=?', attached['id'])
                logs.append(f"Detach: Guild {attached['infos']['title']}")
            else:
                # Bot is on server and attached
                guild = botGuilds[attached['id']]
                self.api.discordAttach(ctx.author, guild, attached)
                logs.append(f"Attach: Guild {attached['infos']['title']} to server {guild.name}")

        content = "\n".join(logs)
        await ctx.author.send(f"""Résultat de la commande `admin sync_guilds`
{content}
""")