# -*- coding: utf-8 -*-

from .mylibs import log
from time import time


class Reaction:
    def __init__(self, client, db, api):
        self.api = api
        self.client = client
        self.db = db

        self.allowedReactions = {
            'no': "🚫",
            'yes': "✅",
            'maybe': "❓",
        }

        self.floodingLimit = 4
        self.floodingTime = 30

        self.cache = {"flooding": {}, "users": {}}

    # Check if user is flooding reaction
    async def _userFlooding(self, user):
        key = user.id
        ts = time()
        floodingCache = self.cache["flooding"]
        if not key in floodingCache or floodingCache[key]['last'] < ts - self.floodingTime:
            floodingCache[key] = {
                'count':0,
                'last': False
            }

        floodingCache[key]['count'] += 1
        floodingCache[key]['last'] = ts

        if floodingCache[key]['count'] >= self.floodingLimit and floodingCache[key]['count'] % 2 == 0:
            await user.send(":stopwatch: C'est le moment d'arrêter de jouer avec les réactions. Merci de patienter quelques minutes.")

        self.cache["flooding"] = floodingCache

        return floodingCache[key]['count'] >= self.floodingLimit

    # get raidplanner user
    # if "False", send a private help message
    async def getRaidplannerUser(self, user, guild, notify=False):
        key = user.id
        ts = time()
        usersCache = self.cache["users"]

        # users in internal cache, return it
        if key in usersCache and usersCache[key]["expire"] > ts:
            return usersCache[key]["value"]

        raidplannerUser = self.db.getUser(user.id, guild.id);
        if raidplannerUser == None and notify:
            await user.send("""Pour pouvoir interragir avec moi, vous devez lier votre compte Raidplanner avec votre compte Discord.
Veuillez cliquer ici pour faire cette connexion : https://mmorga.org/oauth
""")

        usersCache[key] = {
            "value": raidplannerUser,
            "expire": ts + 15
        }

        return raidplannerUser;

    # get all informations about a raw reaction
    async def getReactionInfos(self, payload):
        # user
        user = self.client.get_user(payload.user_id)
        # guild
        guild = self.client.get_guild(payload.guild_id)
        # channel
        channel = guild.get_channel(payload.channel_id)
        # message
        message = await channel.get_message(payload.message_id)

        return user, guild, channel, message

    """
    check if message is an event message managed by bot
    """
    def isEventMessage(self, message):
        result = self.db.fetch('SELECT id FROM events WHERE msg_id=?', message.id)
        if not result:
            return False
        else:
            return True

    """
    analyse user reaction and update subscription to events
    """
    async def on(self, payload):
        # ignore myself and private reaction
        if payload.user_id == self.client.user.id or not payload.guild_id:
            return

        try:
            user, guild, channel, message = await self.getReactionInfos(payload)

            # ignore reaction not on event messages
            if not self.isEventMessage(message):
                return

            # get raidplanner user by api
            raidplannerUser = await self.getRaidplannerUser(user, guild, True)

            # remove reaction if no user connection or not allowed
            if raidplannerUser == None or not payload.emoji.name in self.allowedReactions.values():
                await message.remove_reaction(payload.emoji, user)
                return

            # check flooding
            if await self._userFlooding(user):
                return

            log().info(f"Reaction.on(): Guild=<{guild.name}#{guild.id}>; User=<{user.name}#{user.discriminator}>; Reaction=<{message.id}>; emoji={payload.emoji.name}")

            for reaction in message.reactions:
                reactionUsers = await reaction.users().flatten()
                for reactionUser in reactionUsers:
                    if reactionUser == user and reaction.emoji != payload.emoji.name:
                        await message.remove_reaction(reaction, reactionUser)

        except Exception as e:
            log().error(f"Reaction.on(): user={user.name}; reaction={payload.emoji.name}; exception={str(e)}")

    async def off(self, payload):
        # ignore myself
        if payload.user_id == self.client.user.id or not payload.guild_id:
            return

        # ignore bad reactions
        if not payload.emoji.name in self.allowedReactions.values():
            return

        try:
            user, guild, channel, message = await self.getReactionInfos(payload)

            # ignore reaction not on event messages
            if not self.isEventMessage(message):
                return

            # get raidplanner user by api
            dbUser = await self.getRaidplannerUser(user, guild)

            # remove reaction if no user connection or not allowed
            if dbUser == False or not payload.emoji.name in self.allowedReactions.values():
                return

            # check if user still have a reaction
            hasReaction=False
            for reaction in message.reactions:
                reactionUsers = await reaction.users().flatten()
                for reactionUser in reactionUsers:
                    if reactionUser == user and reaction.emoji != payload.emoji.name:
                        hasReaction=True
                        break
                else:
                    continue
                break

            # no reaction ? API call to "absent"
            if hasReaction == False:
                log().info(f"Reaction.off(): Guild=<{guild.name}#{guild.id}>; User=<{user.name}#{user.discriminator}>; Reaction=<{message.id}>; emoji={payload.emoji.name}")

        except Exception as e:
            log().error(f"Reaction.off(): user={user.name}; reaction={payload.emoji.name}; exception={str(e)}")
