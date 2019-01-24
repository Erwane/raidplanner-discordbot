import src as bot
import sqlite3

Api = bot.Api()

me = Api.user(308664314993180673)
print(f"Me : {me}")

guild = Api.guild(519451096951947264)
print(f"Guild: {guild}")

guild = Api.guild(519451096951947264, "szuKyPHekCklQ+Yir7brOTgJ/IN2JgIu")
print(f"Guild: {guild}")

# events = Api.events(me['id'])
# print(f"{events}")