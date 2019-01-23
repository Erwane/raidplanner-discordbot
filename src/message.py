# -*- coding: utf-8 -*-

from .db import Db
import discord
import re

class Message:
    def __init__(self, api, discordClient):
        self.api = api
        self.client = discordClient

    async def on(self, message):
        # ignore myself
        if message.author == self.client.user:
            return

        command = re.match("^!rp ([^ ]+)( ?)(.*)", message.content.lower())

        # only my commands
        if command != None:
            # print(f"command '{command.group(1)}' by {message.author.id} in {message.channel.id} of {message.guild.id}")
            try:
                await getattr(self, '_%s' % command.group(1))(message)
            except Exception as e:
                return

    async def _help(self, msg):
        myEmbed = discord.Embed(title="Raidplanner help", description="Aide pour le bot Raidplanner", colour=0xff0000)
        try:
            await msg.author.send("this is my help", embed=myEmbed)
        except Exception as e:
            raise e

    async def _me(self, msg):
        print(f"me: {msg.author.id}")

    async def _attach(self, msg):
        # diabled in direct or group message
        if type(msg.channel) != discord.channel.TextChannel:
            return None

        # check for guild owner
        if msg.author != msg.guild.owner:
            await msg.channel.send(f"Désolé {msg.author.name}, vous n'êtes pas le propriétaire de ce serveur.");
            return None

        # author
        author = msg.author
        # guild
        guild = msg.guild

        # direct message
        await author.send("""Pouvez vous me donner votre token Raidplanner ?
Vous trouverez ce token comme ceci :
* allez sur le site https://mmorga.org/guild/my
* cliquez sur "Options et Widget" de la guilde que vous souhaitez lier à ce robot
* copiez le "Token Discord"

""")

        async def askToken(author, guild):
            await author.send("Veuillez saisir votre token de guilde.")

            def checkToken(m):
                return re.match("^[A-Za-z0-9/+]{32}$", m.content.strip())

            try:
                reply = await self.client.wait_for('message', timeout=120.0, check=checkToken)
                rpGuild = self.api.guild(guild.id, reply.content)
                if rpGuild and rpGuild['id'] == guild.id:
                    return True

                return False
            except asyncio.TimeoutError:
                return None

        counter = 0
        while counter < 3:
            result = await askToken(author, guild)

            if result == False:
                counter += 1
                await author.send("Désolé, ce token semble invalide.")
            elif result == True:
                await author.send(f"Merci, votre guilde {guild.name} est maintenant lié au Raidplanner.")
                return
            else:
                counter = 10

        await author.send(f"Session terminé. La guilde {guild.name} n'a pas été liée au Raidplanner.")
