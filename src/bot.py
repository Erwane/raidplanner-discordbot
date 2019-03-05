# -*- coding: utf-8 -*-

from .api import Api
from .db import Db
from .message import Message
from .mylibs import log
from .reaction import Reaction
from .tasks import Tasks
import discord

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
