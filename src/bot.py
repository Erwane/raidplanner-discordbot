
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
        self.api = Api(config)
        self.db = Db(self.api)
        self.Message = Message(self.client, self.db, self.api)
        self.Reaction = Reaction(self.client, self.db, self.api)
        self.Tasks = Tasks(self.client, self.db, self.api)

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

    def run(self):
        self.client.run(self.config['discord']['token'])