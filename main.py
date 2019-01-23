# -*- coding: utf-8 -*-

import discord
import json
import src as bot

with open('config/config.json', 'r') as f:
    config = json.load(f)

client = discord.Client()
api = bot.Api()
Message = bot.Message(api, client)
Reaction = bot.Reaction(api, client)

@client.event  # event decorator/wrapper
async def on_ready():
    print(f"Bot is up as {client.user}")

@client.event
async def on_message(message):
    await Message.on(message)

@client.event
async def on_raw_reaction_add(payload):
    await Reaction.on(payload)

client.run(config['token'])
