
from .mylibs import log

from .api import Api
from .db import Db
from .message import Message
from .reaction import Reaction
from .tasks import Tasks

class Bot:
    def __init__(self, client):
        self.client = client
        self.api = Api()
        self.db = Db()
        self.Message = Message(client, self.db, self.api)
        self.Reaction = Reaction(client, self.db, self.api)
        self.Tasks = Tasks(client, self.db, self.api)

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

    def run(self, token):
        self.client.run(token)