# -*- coding: utf-8 -*-

from .mylibs import log
import asyncio
from datetime import datetime
import discord
import time
from pprint import pprint

class Tasks:
    def __init__(self, bot):
        # bot objects
        self.api = bot.api
        self.client = bot.client
        self.db = bot.db
        self.timing = bot.config['tasks']['interval']

        # reactions
        self.reactionNo = "🚫"
        self.reactionYes = "✅"
        self.reactionMaybe = "❓"

        self._startTasks()

    def _startTasks(self):
        self.client.loop.create_task(self.publishNewEvents())
        self.client.loop.create_task(self.cleanupEvents())

    """
    get events form raidplanner API and publish them on the correct discord guild servers channel
    """
    async def publishNewEvents(self):
        await self.client.wait_until_ready()

        while not self.client.is_closed():
            try:
                events = self.api.nextEvents()
                if len(events):
                    # loop on connected guilds
                    for guild in self.client.guilds:
                        # check if connected and as channel defined
                        guildConnection = self.db.fetch('SELECT rp_token AS discord_token, channel AS channel_id, event_days FROM guilds WHERE id=? AND channel IS NOT NULL', guild.id)
                        if not guildConnection:
                            continue

                        # check if raidplanner guild channel still exists
                        channel = guild.get_channel(guildConnection['channel_id'])
                        if not channel:
                            self.db.query('UPDATE guilds SET channel=NULL WHERE id=?', guild.id)
                            continue

                        for event in events:
                            # event is not for this guild
                            if event['discord_token'] != guildConnection['discord_token']:
                                continue

                            start = datetime.fromtimestamp(event['date_start_timestamp'])
                            now = datetime.now()
                            delta = start - now

                            # publish only event in guild event_days options
                            if delta.days > guildConnection['event_days']:
                                continue

                            title = event['title']
                            dateStart = event['date_start'].strftime('%a %d %b, %Hh%M')

                            if event['is_canceled'] == 1:
                                title = "ANNULÉ : " + title
                                dateStart = "ANNULÉ : " + dateStart

                            eventEmbed = discord.Embed(
                                colour=0x93765d,
                                title=title,
                                url=event['url'],
                                description=event['dungeon_title']
                            ).set_author(
                                name=dateStart,
                                url=event['url']
                            ).set_thumbnail(
                                url=event['game_icon']
                            ).set_footer(
                                text="-> les réactions ne reflètent pas les inscriptions définies directement via le raidplanner ou d'autres applications"
                            )

                            # event description
                            if len(event['description']):
                                eventEmbed.add_field(name='Informations', value=event['description'][:1024])

                            dbEvent = self.db.fetch('SELECT * FROM events WHERE guild_id=? AND event_id=?', guild.id, event['id'])
                            if not dbEvent:
                                # publish event on channel
                                message = await channel.send("@here, un événement vient d'être créé", embed=eventEmbed)

                                # store in db
                                self.db.query('INSERT INTO events (guild_id, event_id, msg_id, modified, event_start) VALUES (?, ?, ?, ?, ?)',
                                    guild.id,
                                    event['id'],
                                    message.id,
                                    event['modified_timestamp'],
                                    event['date_start_timestamp']
                                )
                                log().info(f"event {event['id']} published on {guild.id}#{channel.id} with message id {message.id}")

                                # add reactions
                                await message.add_reaction(self.reactionYes)
                                await message.add_reaction(self.reactionMaybe)
                                await message.add_reaction(self.reactionNo)

                            elif dbEvent['modified'] < event['modified_timestamp']:
                                try:
                                    # modified message event
                                    message = await channel.get_message(dbEvent['msg_id'])

                                    messageText = f"@here, événement modifié {event['modified'].strftime('%A %d à %Hh')}"

                                    if event['is_canceled'] == 1:
                                        messageText = f"@here, cet événement est **annulé** :octagonal_sign:"

                                    await message.edit(content=messageText, embed=eventEmbed)

                                    # store new informations
                                    self.db.query('UPDATE events SET modified=?, event_start=?',
                                        event['modified_timestamp'],
                                        event['date_start_timestamp']
                                    )
                                    log().info(f"event {event['id']} modified on {guild.id}#{channel.id} with message id {message.id}")

                                    # date start change for 2 hours
                                    if abs(dbEvent['event_start'] - event['date_start_timestamp']) > (3600 * 2):
                                        # remove all reactions
                                        for reaction in message.reactions:
                                            reactionUsers = await reaction.users().flatten()
                                            for reactionUser in reactionUsers:
                                                if reactionUser != self.client.user:
                                                    await message.remove_reaction(reaction, reactionUser)

                                except Exception as e:
                                    log().error(f"failed to edit event {dbEvent['id']} on message {dbEvent['msg_id']} : {str(e)}")

                await asyncio.sleep(self.timing)
            except Exception as e:
                log().error(f"Tasks.publishNewEvents: {str(e)}")
                await asyncio.sleep(self.timing)

    """
    get events form raidplanner API and publish them on the correct discord guild servers channel
    """
    async def cleanupEvents(self):
        await self.client.wait_until_ready()

        while not self.client.is_closed():
            try:
                # remove from db
                self.db.query('DELETE FROM events WHERE event_start<?', int(time.time() - 86400 * 2))

                await asyncio.sleep(self.timing)
            except Exception as e:
                log().error(str(e))
                await asyncio.sleep(self.timing)
