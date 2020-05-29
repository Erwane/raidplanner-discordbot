# -*- coding: utf-8 -*-

from .api import Api
from .db import Db
from .admin import Admin
from .message import Message
from .mylibs import log
from .reaction import Reaction
from .tasks import Tasks
import discord
from discord.ext import commands
from pprint import pprint

class Bot:
    def __init__(self, config):
        self.config = config
        self.client = commands.Bot(command_prefix=config['prefix'], owner_ids=config['owners'])
        self.db = Db(self)
        self.api = Api(self)
        self.Message = Message(self)
        self.Reaction = Reaction(self)
        self.Tasks = Tasks(self)

        self.initEvents()

    def initEvents(self):
        @self.client.event  # event decorator/wrapper
        async def on_ready():
            log().info(f"Bot is up as {self.client.user} with version {discord.version_info}")

        @self.client.event
        async def on_raw_reaction_add(payload):
            await self.Reaction.on(payload)

        @self.client.event
        async def on_raw_reaction_remove(payload):
            await self.Reaction.off(payload)

        @self.client.event
        async def on_guild_remove(guild):
            self.detach(guild)

        # Me
        @self.client.command()
        async def me(ctx):
            await ctx.author.send(f"Votre id discord: {ctx.author.id}")

        # Bot status
        @self.client.command()
        async def status(self, msg):
            await self.bot.status(msg)

        # Setup: attach bot to guild
        @self.client.command()
        async def attach(self, msg):
            setup = Setup(self.bot)
            await setup.attach(msg)

        # Setup: detach bot from guild
        @self.client.command()
        async def detach(self, msg):
            setup = Setup(self.bot)
            await setup.detach(msg)

        @self.client.command()
        async def _chan(self, msg):
            setup = Setup(self.bot)
            await setup.chan(msg)

        @self.client.command()
        async def _days(self, msg):
            setup = Setup(self.bot)
            await setup.days(msg)

        @self.client.command(name="admin")
        async def admin(ctx, *args):
            is_owner = await self.client.is_owner(ctx.author)
            if not is_owner:
                return False

            raidplannerAdmin = await self.getRaidplannerUser(ctx.author, notify=True)
            if not raidplannerAdmin:
                return False

            try:
                admin = Admin(self);
                args = list(args)
                command = args.pop(0)
                await getattr(admin, command)(ctx, args)
            except Exception as e:
                pprint(e)
                await ctx.send(f"Cette sous-commande `{command}` admin n'existe pas, ou elle a plantée.")
                return False

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