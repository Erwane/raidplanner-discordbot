# -*- coding: utf-8 -*-

from config.config import Config
from .api import Api
from .db import Db
from .admin import Admin
from .mylibs import log
from .reaction import Reaction
from .setup import Setup
from .tasks import Tasks
import discord
from discord.ext import commands


class Bot:
    __config = None

    def __init__(self):
        self.__config = Config.read()
        self.client = commands.Bot(command_prefix=self.__config['prefix'], owner_ids=self.__config['owners'])
        self.client.remove_command('help')
        self.bot = self.client
        self.db = Db(self)
        self.api = Api(self)
        self.Reaction = Reaction(self)
        self.Tasks = Tasks(self)

        self.initEvents()

    def initEvents(self):
        @self.client.event  # event decorator/wrapper
        async def on_ready():
            log().info(f"Bot is up as {self.client.user} with version discord.py {discord.__version__}")

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
        @self.client.command(hidden=True)
        async def me(ctx):
            await ctx.author.send(f"Votre id discord: {ctx.author.id}")

        # Bot status
        @self.bot.command(brief="Statut du bot.")
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
        @self.client.command(brief="Lie le bot à votre guilde Raidplanner MMOrga.")
        async def attach(ctx):
            setup = Setup(self)
            await setup.attach(ctx.message)

        # Setup: detach bot from guild
        @self.client.command(brief="Détache le bot de votre guilde Raidplanner MMOrga.")
        async def detach(ctx):
            setup = Setup(self)
            await setup.detach(ctx.message)

        @self.client.command(brief="Configure le canal de sortie des événenemts.")
        async def chan(ctx):
            setup = Setup(self)
            await setup.chan(ctx.message)

        @self.client.command(brief="Configure le délai de publication d'un événement.")
        async def days(ctx):
            setup = Setup(self)
            await setup.days(ctx.message)

        @self.client.command(name="admin", hidden=True)
        async def admin(ctx, *args):
            is_owner = await self.client.is_owner(ctx.author)
            if not is_owner:
                return False

            raidplannerAdmin = await self.getRaidplannerUser(ctx.author, notify=True)
            if not raidplannerAdmin:
                return False

            command = None
            try:
                admin = Admin(self)
                args = list(args)
                command = args.pop(0)
                await getattr(admin, command)(ctx, args)
            except Exception as e:
                log().error(f"{e}")
                await ctx.author.send(f"Cette sous-commande `{command}` admin n'existe pas, ou elle a plantée.")
                return False

        @status.error
        async def private_message_error(ctx, error):
            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send('Désolé, cette commande doit être utilisé sur un serveur discord.')

        @self.bot.command()
        async def help(ctx):
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

            await ctx.author.send("", embed=myEmbed)

    def run(self):
        self.client.run(self.__config['discord']['token'])

    """
    Check if author is server owner
    """
    async def checkServerOwner(self, message, notify=False):
        # disabled in direct or group message
        if not isinstance(message.channel, discord.channel.TextChannel):
            await message.author.send(f"Désolé, cette commande doit être utilisé sur un serveur discord.");
            return False

        # check for guild server owner
        if message.author.id != message.channel.guild.owner_id:
            if notify:
                await message.channel.send(
                    f"Désolé {message.author.name}, vous n'êtes pas le propriétaire de ce serveur."
                )
            return False

        return True

    """
    Get Raidplanner user from DB/API.
    Notify to connect if not
    """
    async def getRaidplannerUser(self, discordUser, notify=False):
        raidplannerUser = self.db.getUser(discordUser.id);

        if not raidplannerUser and notify:
            await discordUser.send(
                "Pour pouvoir interragir avec moi, vous devez lier votre compte Raidplanner avec votre compte "
                "Discord.\n "
                "Veuillez cliquer ici pour faire cette connexion : https://mmorga.org/oauth/discord")
        return raidplannerUser
