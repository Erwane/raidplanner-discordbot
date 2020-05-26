# -*- coding: utf-8 -*-

from .mylibs import log
import asyncio
import discord
import re
from pprint import pprint

class Setup:
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db

    """
    Vérifie que le message est initié depuis un serveur discord
    et qu'il provient du owner de ce serveur
    """
    async def _checkOwner(self, msg):
        # disabled in direct or group message
        if type(msg.channel) != discord.channel.TextChannel:
            await msg.author.send(f"Désolé, cette commande doit être utilisé sur un serveur discord.");
            return False

        # check for guild owner
        if msg.author != msg.guild.owner:
            await msg.author.send(f"Désolé {msg.author.name}, vous n'êtes pas le propriétaire de ce serveur.");
            return False

        return True

    # Attach discord guild to Raidplanner
    async def attach(self, msg):
        if not await self._checkOwner(msg):
            return False

        # author
        author = msg.author

        # Linked user ?
        raidplannerAuthor = await self.bot.getRaidplannerUser(author, True)

        pprint(dict(raidplannerAuthor))

        if not raidplannerAuthor:
            return False

        # guild
        guild = msg.guild

        # direct message
        await author.send("""Pouvez vous me donner votre token Raidplanner ?
Vous trouverez ce token comme ceci :
* allez sur le site <https://mmorga.org/guild/my>
* cliquez sur "Options et Widget" de la guilde que vous souhaitez lier à ce robot
* copiez le "Token Discord"

""")

        async def askToken(author, guild):
            await author.send("Veuillez saisir votre token de guilde.")

            def checkToken(m):
                return re.match("^[A-Za-z0-9]{32}$", m.content.strip())

            try:
                # wait for owner reply
                reply = await self.client.wait_for('message', timeout=120.0, check=checkToken)

                # get raiplanner guild
                raidplannerGuild = self.db.getGuild(guild.id, reply.content.strip())

                if raidplannerGuild:
                    if raidplannerGuild['id'] == guild.id:
                        return 'attached'
                    else:
                        return 'already_attached'

                return 'not_found'
            except asyncio.TimeoutError as e:
                return 'timeout'

        counter = 0
        while counter < 3:
            result = await askToken(author, guild)

            if result == 'not_found':
                counter += 1
                await author.send("Désolé, ce token semble invalide.")
            elif result == 'already_attached':
                return await author.send(f"Désolé, ce token est déjà utilisé sur un autre serveur discord.")
            elif result == 'attached':
                return await author.send(f"Merci, votre serveur discord **{guild.name}** est maintenant lié au Raidplanner.")
            else:
                counter = 10

        await author.send(f"Session terminé. Le serveur discord **{guild.name}** n'a pas été lié au Raidplanner.")

    """
    detach Raidplanner from discord
    """
    async def detach(self, msg):
        if not await self._checkOwner(msg):
            return False

        guild = msg.guild
        channel = msg.channel

        self.bot.detach(guild)

        await channel.send(f"Cette guilde n'est plus liée et je ne publierai plus d'événement. Utilisez `!rp attach` pour me rattacher à cette guilde.")


    # assign an events channel for bot
    # check permission before attach
    async def chan(self, msg):
        if not await self._checkOwner(msg):
            return False

        # vars
        author = msg.author
        guild = msg.guild
        channel = msg.channel

        guildToken = self.db.getTokenGuild(guild.id)

        if not guildToken:
            await channel.send("""Vous devez attacher ce serveur discord au bot avec la commande `!rp attach`""")
            return False

        await channel.send("""Veuillez m'indiquer sur quel canal je dois publier les événements ?
exemple : `#raidplanner`

Pour que le service fonctionne bien, voici les droits requis dans ce canal :
```
@membres :
    - lire les messages uniquement
@RaidplannerBot :
    - lire les messages
    - envoyer des messages
    - gérer les messages
    - voir les anciens messages
    - mentionner @everyone (n'utilise que @here)
    - ajouter des réactions
```
""")

        async def ask(author, guild):
            def checkAnswer(m):
                match = re.match("^<#(\d+)>", m.content.strip())
                if not match:
                    return False

                for chan in m.guild.channels:
                    if chan.id == int(match.group(1)):
                        return chan.id

                return False

            try:
                reply = await self.client.wait_for('message', timeout=120.0, check=checkAnswer)

                # extract and return channel id
                match = re.match("^<#(\d+)>", reply.content.strip())

                return int(match.group(1))
            except asyncio.TimeoutError as e:
                return 'timeout'

        counter = 0
        while counter < 3:
            channelId = await ask(author, guild)

            if channelId > 0:
                try:
                    botChannel = guild.get_channel(channelId)
                    permissions = guild.me.permissions_in(botChannel)

                    missingPermissions = []

                    if not permissions.read_messages:
                        missingPermissions.append("**Lecture** : Lire les messages")

                    if not permissions.send_messages:
                        missingPermissions.append("**Ecriture** : Envoyer des messages")

                    if not permissions.manage_messages:
                        missingPermissions.append("**Manage** : Gérer les messages")

                    if not permissions.read_message_history:
                        missingPermissions.append("**Historique** : Voir les anciens messages")

                    if not permissions.mention_everyone:
                        missingPermissions.append("**Mention** : Mentionner `@everyone` (n'utilise que `@here`)")

                    if not permissions.add_reactions:
                        missingPermissions.append("**Réaction** : Ajouter des réactions")

                    if len(missingPermissions):
                        msg = f"Désolé, il me manque les permissions suivantes dans le canal <#{channelId}>."
                        return await channel.send(msg + "\n- " + "\n- ".join(missingPermissions))

                    # attach channel id to guild id
                    self.db.query('UPDATE guilds SET channel=? WHERE id=?', channelId, guild.id)
                    log().info(f"{author.name}#{author.discriminator} give bot channel #{botChannel.name}<{botChannel.id}> in guild <{guild.id}>")

                    return await channel.send(f"Merci, je publierai les événements dans le canal <#{channelId}>.")
                except Exception as e:
                    log().error(str(e))
            else:
                counter = 10

        await channel.send(f"Session terminé. Le Raidplanner n'a pas trouvé de canal adéquat.")

    """
    nombre de jour pour qu'un événement soit publié
    """
    async def days(self, msg):
        if not await self._checkOwner(msg):
            return False

        # vars
        guild = msg.guild
        channel = msg.channel

        await channel.send("""Publier les événements qui ont lieu dans combien de jours ? (saisir un nombre entre **1** et **15**)""")

        async def ask():
            def checkAnswer(m):
                match = re.match("^(\d+)$", m.content.strip())
                if match:
                    d = int(match.group(1))
                    if d >= 1 and d <= 15:
                        return True

                return False

            try:
                reply = await self.client.wait_for('message', timeout=30.0, check=checkAnswer)

                return int(reply.content.strip())
            except asyncio.TimeoutError as e:
                return False

        days = await ask()

        if days != False:
            self.db.query('UPDATE guilds SET event_days=? WHERE id=?', days, guild.id)
            await channel.send("""C'est enregistré.""")
        else:
            await channel.send("""Ce n'est pas un nombre.""")
