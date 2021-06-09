# -*- coding: utf-8 -*-

from .mylibs import log
import asyncio
import re


class Setup:
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db

    # Attach discord guild to Raidplanner
    async def attach(self, msg):
        # if not await self.bot.checkServerOwner(msg, True):
        #     return False

        # author
        author = msg.author

        # Linked user ?
        raidplanner_author = await self.bot.getRaidplannerUser(author, True)

        if not raidplanner_author:
            return False

        # guild
        guild = msg.guild
        raidplanner_guild = self.db.getGuild(guild.id)

        if raidplanner_guild:
            await msg.channel.send(f"Le serveur discord **{guild.name}** est déjà lié au Raidplanner.")
            return True

        # direct message
        await author.send("""Pouvez vous me donner votre token Raidplanner ?
Vous trouverez ce token comme ceci :
* allez sur le site <https://mmorga.org/guild/my>
* cliquez sur "Options et Widget" de la guilde que vous souhaitez lier à ce robot
* copiez le "Token Discord"

""")

        counter = 0
        while counter < 3:
            status, raidplanner_guild = await self.__ask_token(author, guild)

            if status == 'not_found':
                counter += 1
                await author.send("Désolé, ce token semble invalide.")
            elif status == 'already_attached':
                return await author.send(f"Désolé, ce token est déjà utilisé sur un autre serveur discord.")
            elif status == 'attached':
                self.api.discordAttach(author, guild, raidplanner_guild)
                await author.send("Token validé")
                return await msg.channel.send(
                    f"Merci, votre serveur discord **{guild.name}** est maintenant lié au Raidplanner.")
            else:
                counter = 10

        await author.send("Session terminé.")
        await msg.channel.send(f"Le serveur discord **{guild.name}** n'a pas été lié au Raidplanner.")

    async def __ask_token(self, author, guild):
        await author.send("Veuillez saisir votre token de guilde.")

        def check_token(m):
            return re.match("^[A-Za-z0-9]{32}$", m.content.strip())

        try:
            # wait for owner reply
            reply = await self.client.wait_for('message', timeout=10.0, check=check_token)

            # get raiplanner guild
            raidplanner_guild = self.db.getGuild(guild.id, reply.content.strip())

            if raidplanner_guild:
                if raidplanner_guild['id'] == guild.id:
                    return 'attached', raidplanner_guild
                else:
                    return 'already_attached', False

            return 'not_found', False
        except asyncio.TimeoutError:
            return 'timeout', False

    """
    Detach bot from discord
    """
    async def detach(self, msg):
        if not await self.bot.checkServerOwner(msg, True):
            return False

        # author
        author = msg.author
        raidplanner_author = await self.bot.getRaidplannerUser(author, True)
        if not raidplanner_author:
            return False

        # guild
        guild = msg.guild
        raidplanner_guild = self.db.getGuild(guild.id)

        if not raidplanner_guild:
            await msg.channel.send(f"Le serveur discord **{guild.name}** n'est pas lié au Raidplanner.")
            return True

        # Wait owner response
        try:
            await msg.channel.send(
                f"Le bot sera détaché de **{guild.name}** et toutes les données du bot seront supprimées. **Êtes vous "
                f"sur ?** (`Y|Yes|O|Oui` / `N|No|Non`)")
            reply = await self.client.wait_for('message', timeout=5.0)
            response = reply.content.strip()
            if re.match("^Y|Yes|O|Oui$", response, flags=re.IGNORECASE):
                # Detach bot
                self.api.discordDetach(author, guild, raidplanner_guild)
                self.db.detachBot(guild.id)
                await msg.channel.send(f"Le serveur discord **{guild.name}** n'est plus lié au bot.")
            else:
                await msg.channel.send("Ouf :)")
        except Exception:
            await msg.channel.send("Ouf :)")

    # assign an events channel for bot
    # check permission before attach
    async def chan(self, msg):
        # if not await self.bot.checkServerOwner(msg, True):
        #     return False

        # vars
        author = msg.author
        guild = msg.guild
        channel = msg.channel

        guild_token = self.db.getTokenGuild(guild.id)

        if not guild_token:
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

        async def ask():
            def check_answer(m):
                matches = re.match("^<#([0-9]+)>", m.content.strip())
                if not matches:
                    return False

                for chan in m.guild.channels:
                    if chan.id == int(matches.group(1)):
                        return chan.id

                return False

            try:
                reply = await self.client.wait_for('message', timeout=120.0, check=check_answer)

                # extract and return channel id
                match = re.match("^<#([0-9]+)>", reply.content.strip())

                return int(match.group(1))
            except asyncio.TimeoutError:
                return 'timeout'

        counter = 0
        while counter < 3:
            channel_id = await ask()

            if channel_id > 0:
                try:
                    bot_channel = guild.get_channel(channel_id)
                    permissions = guild.me.permissions_in(bot_channel)

                    missing_permissions = []

                    if not permissions.read_messages:
                        missing_permissions.append("**Lecture** : Lire les messages")

                    if not permissions.send_messages:
                        missing_permissions.append("**Écriture** : Envoyer des messages")

                    if not permissions.manage_messages:
                        missing_permissions.append("**Manage** : Gérer les messages")

                    if not permissions.read_message_history:
                        missing_permissions.append("**Historique** : Voir les anciens messages")

                    if not permissions.mention_everyone:
                        missing_permissions.append("**Mention** : Mentionner `@everyone` (n'utilise que `@here`)")

                    if not permissions.add_reactions:
                        missing_permissions.append("**Réaction** : Ajouter des réactions")

                    if len(missing_permissions):
                        msg = f"Désolé, il me manque les permissions suivantes dans le canal <#{channel_id}>."
                        return await channel.send(msg + "\n- " + "\n- ".join(missing_permissions))

                    # attach channel id to guild id
                    self.db.query('UPDATE guilds SET channel=? WHERE id=?', channel_id, guild.id)
                    log().info(
                        f"{author.name}#{author.discriminator} give bot channel #{bot_channel.name}<{bot_channel.id}> "
                        f"in guild <{guild.id}>")

                    return await channel.send(f"Merci, je publierai les événements dans le canal <#{channel_id}>.")
                except Exception as e:
                    log().error(str(e))
            else:
                counter = 10

        await channel.send(f"Session terminé. Le Raidplanner n'a pas trouvé de canal adéquat.")

    """
    nombre de jour pour qu'un événement soit publié
    """
    async def days(self, msg):
        # if not await self.bot.checkServerOwner(msg, True):
        #     return False

        # vars
        guild = msg.guild
        channel = msg.channel

        await channel.send(
            """Publier les événements qui ont lieu dans combien de jours ? (saisir un nombre entre **1** et **15**)""")

        async def ask():
            def check_answer(m):
                match = re.match("^([0-9]+)$", m.content.strip())
                if match:
                    d = int(match.group(1))
                    if 1 <= d <= 15:
                        return True

                return False

            try:
                reply = await self.client.wait_for('message', timeout=30.0, check=check_answer)

                return int(reply.content.strip())
            except asyncio.TimeoutError:
                return False

        days = await ask()

        if days:
            self.db.query('UPDATE guilds SET event_days=? WHERE id=?', days, guild.id)
            await channel.send("""C'est enregistré.""")
        else:
            await channel.send("""Ce n'est pas un nombre.""")
