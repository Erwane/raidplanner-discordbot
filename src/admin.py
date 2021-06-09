# -*- coding: utf-8 -*-

"""
Admin commands
"""


class Admin:
    def __init__(self, bot):
        self.bot = bot.client
        self.api = bot.api
        self.db = bot.db

    # noinspection PyUnusedLocal
    async def status(self, ctx, args=None):
        servers = self.bot.guilds
        guilds = self.db.fetchall("SELECT id FROM guilds")
        events = self.db.fetchall("SELECT id FROM events")

        if not guilds:
            guilds = []
        if not events:
            events = []

        output = f"""Serveurs connectés : {len(servers)}
Guilde liées : {len(guilds)}
Événements gérés : {len(events)}
"""
        await ctx.author.send(output)

    # noinspection PyUnusedLocal
    async def sync_guilds(self, ctx, args=None):
        attached_guilds = dict()
        rows = self.db.fetchall("SELECT id, rp_token, response FROM guilds")
        for row in rows:
            attached_guilds[row['id']] = row

        bot_guilds = dict()
        for guild in self.bot.guilds:
            bot_guilds[guild.id] = guild

        logs = []

        for key, attached in attached_guilds.items():
            if not attached['id'] in bot_guilds:
                # Remove guild from DB
                self.db.detachBot(attached['id'])

                # Call api detach (clean the discord_server field)
                self.api.discordDetach(ctx.author, False, attached)

                logs.append(f"Detach: Guild {attached['infos']['title']}")
            else:
                # Bot is on server and attached
                guild = bot_guilds[attached['id']]
                self.api.discordAttach(ctx.author, guild, attached)
                logs.append(f"Attach: Guild {attached['infos']['title']} to server {guild.name}")

        content = "\n".join(logs)
        await ctx.author.send(f"""Résultat de la commande `admin sync_guilds`
{content}
""")
