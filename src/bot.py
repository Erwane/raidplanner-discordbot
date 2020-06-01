# -*- coding: utf-8 -*-

from .api import Api
from .db import Db
from .admin import Admin
from .message import Message
from .mylibs import log
from .reaction import Reaction
from .setup import Setup
from .tasks import Tasks
import discord
from discord.ext import commands
from pprint import pprint

class Bot:
    def __init__(self, config):
        self.config = config
        self.client = commands.Bot(command_prefix=config['prefix'], owner_ids=config['owners'])
        self.bot = self.client
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
            raidplannerGuild = self.db.getGuild(guild.id)

            # Clean DB
            self.db.detachBot(guild.id)

            if raidplannerGuild:
                self.api.discordDetach(False, guild, raidplannerGuild)

        # Me
        @self.client.command()
        async def me(ctx):
            await ctx.author.send(f"Votre id discord: {ctx.author.id}")

        # Bot status
        @self.bot.command()
        @commands.guild_only()
        async def status(ctx):
            channel = ctx.message.channel
            guild = ctx.message.guild

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

        # Setup: attach bot to guild
        @self.client.command()
        async def attach(ctx):
            setup = Setup(self)
            await setup.attach(ctx.message)

        # Setup: detach bot from guild
        @self.client.command()
        async def detach(ctx):
            setup = Setup(self)
            await setup.detach(ctx.message)

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

        @status.error
        async def private_message_error(ctx, error):
            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send('Désolé, cette commande doit être utilisé sur un serveur discord.')

    def run(self):
        self.client.run(self.config['discord']['token'])

    """
    Check if author is server owner
    """
    async def checkServerOwner(self, message, notify=False):
        # disabled in direct or group message
        if not isinstance(message.channel, discord.channel.TextChannel):
            await message.author.send(f"Désolé, cette commande doit être utilisé sur un serveur discord.");
            return False

        # check for guild server owner
        if message.author != message.guild.owner:
            if notify:
                await message.author.send(f"Désolé {message.author.name}, vous n'êtes pas le propriétaire de ce serveur.");
            return False

        return True

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
