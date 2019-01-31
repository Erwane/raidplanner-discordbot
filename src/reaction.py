# -*- coding: utf-8 -*-

from .mylibs import log
from pprint import pprint
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

        self.floodingLimit = 4;
        self.floodingTime = 30;

        self.flooding = {}

    async def _userFlooding(self, user):
        key = user.id
        ts = time()
        if not key in self.flooding or self.flooding[key]['last'] < ts - self.floodingTime:
            self.flooding[key] = {
                'count':0,
                'last': False
            }

        self.flooding[key]['count'] += 1
        self.flooding[key]['last'] = ts

        if self.flooding[key]['count'] >= self.floodingLimit and self.flooding[key]['count'] % 2 == 0:
            await user.send(":stopwatch: C'est le moment d'arrêter de jouer avec les réactions. Merci de patienter quelques minutes.")

        return self.flooding[key]['count'] >= self.floodingLimit

    # 308664314993180673 react on 535753694982176789 with reaction: ✅
    async def on(self, payload):
        # ignore myself
        if payload.user_id == self.client.user.id or not payload.guild_id:
            return

        try:
            # user
            user = self.client.get_user(payload.user_id)
            # guild
            guild = self.client.get_guild(payload.guild_id)
            # channel
            channel = guild.get_channel(payload.channel_id)
            # message
            message = await channel.get_message(payload.message_id)

            # remove reaction if not allowed
            if not payload.emoji.name in self.allowedReactions.values():
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
            log().error(f"Reaction.on(): {str(e)}")

    async def off(self, payload):
        # ignore myself
        if payload.user_id == self.client.user.id or not payload.guild_id:
            return

        # ignore bad reactions
        if not payload.emoji.name in self.allowedReactions.values():
            return

        try:
            # user
            user = self.client.get_user(payload.user_id)
            # guild
            guild = self.client.get_guild(payload.guild_id)
            # channel
            channel = guild.get_channel(payload.channel_id)
            # message
            message = await channel.get_message(payload.message_id)

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
            log().error(f"Reaction.off(): {str(e)}")


