# -*- coding: utf-8 -*-

from .mylibs import log
import asyncio
import discord
import re

class Setup:
    def __init__(self, client, db, api):
        self.api = api
        self.client = client
        self.db = db

    """
    Vérifie que le message est initié depuis un serveur discord
    et qu'il provient du owner de ce serveur
    """
    async def _checkOwner(self, msg):
        # disabled in direct or group message
        if type(msg.channel) != discord.channel.TextChannel:
            await msg.author.send(f"Désolé, cette commande doit être utilisé sur un serveur discord.");
            return None

        # check for guild owner
        if msg.author != msg.guild.owner:
            await msg.author.send(f"Désolé {msg.author.name}, vous n'êtes pas le propriétaire de ce serveur.");
            return None

        return True

    async def attach(self, msg):
        if not await self._checkOwner(msg):
            return None

        # author
        author = msg.author
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
                reply = await self.client.wait_for('message', timeout=120.0, check=checkToken)
                rpGuild = self.api.guild(guild.id, reply.content)
                if rpGuild:
                    if rpGuild['id'] == guild.id:
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

    async def chan(self, msg):
        if not await self._checkOwner(msg):
            return None

        # vars
        author = msg.author
        guild = msg.guild
        channel = msg.channel

        currentValue = self.db.fetch('SELECT * FROM guilds WHERE id=?', guild.id)
        if not currentValue or currentValue['rp_token'] == '':
            await channel.send("""Vous devez attaché ce serveur discord au bot avec la commande `!rp attach`""")
            return None

        await channel.send("""Veuillez m'indiquer sur quel canal je dois publier les événements ?
exemple : `#raidplanner`

Pour une utilisation optimale du service, je vous recommande un canal avec ces permissions afin de toujours voir les événements en cours :
```
@membres :
    - peut ajouter des réactions
    - ne peut pas envoyer de message
@RaidplannerBot :
    - peut ajouter des réactions
    - peut envoyer des messages
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

                    if not permissions.add_reactions:
                        return await channel.send(f"Désolé, je n'ai pas le droit d'ajouter des réactions dans le canal <#{channelId}>.")

                    if not permissions.send_messages:
                        return await channel.send(f"Désolé, je n'ai pas le droit d'écrire dans le canal <#{channelId}>.")

                    # attach channel id to guild id
                    self.db.update('UPDATE guilds SET channel=? WHERE id=?', channelId, guild.id)

                    log().info(f"{author.name}#{author.discriminator} give bot channel #{botChannel.name}<{botChannel.id}> in guild <{guild.id}>")

                    return await channel.send(f"Merci, je publierai les événements dans le canal <#{channelId}>.")
                except Exception as e:
                    log().error(str(e))
            else:
                counter = 10

        await channel.send(f"Session terminé. Le Raidplanner n'a pas trouvé de canal adéquat.")