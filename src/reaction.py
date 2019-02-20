# -*- coding: utf-8 -*-

from .mylibs import log
from time import time
from pprint import pprint


class Reaction:
    def __init__(self, bot):
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db

        self.allowedReactions = {
            'no': "🚫",
            'yes': "✅",
            'maybe': "❓",
        }

        self.floodingLimit = 4
        self.floodingTime = 30

        self.cache = {"flooding": {}, "users": {}}

    # get the emoji reaction key
    def _getReactionStatus(self, emoji):
        for k, v in self.allowedReactions.items():
            if v == emoji:
                return k

        return None

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
    async def getRaidplannerUser(self, user, notify=False):
        key = user.id
        ts = time()
        usersCache = self.cache["users"]

        # users in internal cache, return it
        if key in usersCache and usersCache[key]["expire"] > ts:
            return usersCache[key]["value"]

        raidplannerUser = self.db.getUser(user.id);
        if raidplannerUser == None and notify:
            await user.send("""Pour pouvoir interragir avec moi, vous devez lier votre compte Raidplanner avec votre compte Discord.
Veuillez cliquer ici pour faire cette connexion : https://mmorga.org/oauth
""")

        self.cache["users"][key] = {
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
    get event attached to this message
    """
    def getEventMessage(self, message):
        result = self.db.fetch('SELECT * FROM events WHERE msg_id=?', message.id)
        if not result:
            return False
        else:
            return result

    """
    analyse user reaction and update subscription to events
    """
    async def on(self, payload):
        # ignore myself and private reaction
        if payload.user_id == self.client.user.id or not payload.guild_id:
            return

        try:
            user, guild, channel, message = await self.getReactionInfos(payload)
            event = self.getEventMessage(message)

            # ignore reaction not on event messages
            if not event:
                return

            # get raidplanner user by api
            raidplannerUser = await self.getRaidplannerUser(user, notify=True)

            # remove reaction if no user connection or not allowed
            if raidplannerUser == None or not payload.emoji.name in self.allowedReactions.values():
                await message.remove_reaction(payload.emoji, user)
                return

            # check flooding
            if await self._userFlooding(user):
                return

            # set presence via API
            self.api.setPresence(event['event_id'], raidplannerUser['rp_id'], self._getReactionStatus(payload.emoji.name), guild.id)
            # log it if ok
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
            event = self.getEventMessage(message)

            # ignore reaction not on event messages
            if not event:
                return

            # get raidplanner user by api
            dbUser = await self.getRaidplannerUser(user)

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
