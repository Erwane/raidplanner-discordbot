# -*- coding: utf-8 -*-

from .api import Api
from .db import Db
from .message import Message
from .mylibs import log
from .reaction import Reaction
from .tasks import Tasks
import discord
from pprint import pprint

class Bot:
    def __init__(self, config):
        self.config = config
        self.client = discord.Client()
        self.db = Db(self)
        self.api = Api(self)
        self.Message = Message(self)
        self.Reaction = Reaction(self)
        self.Tasks = Tasks(self)

        self.initEvents()

    def initEvents(self):
        @self.client.event  # event decorator/wrapper
        async def on_ready():
            log().info(f"Bot is up as {self.client.user}")

        @self.client.event
        async def on_message(message):
            await self.Message.on(message)

        @self.client.event
        async def on_raw_reaction_add(payload):
            await self.Reaction.on(payload)

        @self.client.event
        async def on_raw_reaction_remove(payload):
            await self.Reaction.off(payload)

        @self.client.event
        async def on_guild_remove(guild):
            self.detach(guild)

    def run(self):
        self.client.run(self.config['discord']['token'])

    """
    detach bot from guild server
    """
    def detach(self, guild):
        self.db.query('DELETE FROM events WHERE guild_id=?', guild.id)
        self.db.query('DELETE FROM guilds WHERE id=?', guild.id)

    """
    Get Raidplanner user from DB/API.
    Notify to connect if not
    """
    async def getRaidplannerUser(self, discordUser, notify=False):
        raidplannerUser = self.db.getUser(discordUser.id);

        if not raidplannerUser and notify:
            await discordUser.send("""Pour pouvoir interragir avec moi, vous devez lier votre compte Raidplanner avec votre compte Discord.
Veuillez cliquer ici pour faire cette connexion : https://mmorga.org/oauth
""")
        return raidplannerUser

    """
    Get bot status for this server
    """
    async def status(self, msg):
        channel = msg.channel
        guild = msg.guild

        raidplannerGuild = self.db.getGuild(guild.id)
        if not raidplannerGuild:
            await channel.send("Le bot n'est pas encore lié à ce serveur.")
        else:
            guildTitle = raidplannerGuild['infos']['title']
            events = self.db.fetch('SELECT count(id) as total FROM events WHERE guild_id=?', guild.id)
            countEvent = events['total']
            await channel.send(f"""Ce serveur est lié à la guilde **{guildTitle}** sur MMOrga Raidplanner.
Le bot a géré `{countEvent}` événement(s).
""")