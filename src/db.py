# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import time

class Db:
    def __init__(self, api):
        dbPath = os.getcwd() + '/resources/bot.db'
        self.db = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

        self.createTable("""users ("id" PK INTEGER NOT NULL, "rp_id" INTEGER, "response" TEXT, "expire" INTEGER)""")
        self.createTable("""guilds ("id" PK INTEGER NOT NULL, "rp_token" TEXT, "response" TEXT, "channel" INTEGER, "expire" INTEGER)""")
        self.createTable("""events ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "guild_id" INTEGER NOT NULL, "event_id" INTEGER NOT NULL, "msg_id" INTEGER NOT NULL, "modified" INTEGER, "event_start" INTEGER)""")

        self.api = api

    # close database connection on exit
    def __del__(self):
        self.db.close()

    # create table
    def createTable(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS %s" % query)
            self.db.commit()
        except Exception as e:
            raise e

    # fetch one row
    def fetch(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            return c.fetchone()
        except Exception as e:
            raise e

    # execute query
    def query(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            self.db.commit()
        except Exception as e:
            raise e

    # get guild from DB or API if don't exists
    def getGuild(self, guildId, raidplannerToken=None):
        currentValue = self.fetch("SELECT id FROM guilds WHERE id=?", guildId)

        # with Raidplanner Token
        if raidplannerToken:
            # from db
            guild = self.fetch("SELECT * FROM guilds WHERE rp_token=?", raidplannerToken)
            if not guild:
                # from api
                fromApi = self.api.getGuild(raidplannerToken)

                # nothing exists
                if not fromApi:
                    return None

                # store api result
                expire = int(time.time()) + (3600 * 24 * 7)
                if not currentValue:
                    self.query('INSERT INTO guilds (id, rp_token, response, expire) VALUES(?, ?, ?, ?)',
                        guildId, raidplannerToken, json.dumps(fromApi['response']), expire
                    )
                else:
                    self.query('UPDATE guilds SET rp_token=?, response=?, expire=? WHERE id=?',
                        raidplannerToken, json.dumps(fromApi['response']), expire, guildId
                    )

            # redo currentValue after api update
            currentValue = self.fetch("SELECT id FROM guilds WHERE id=?", guildId)

        return currentValue

    # get raidplanner guild token
    def getTokenGuild(self, guildId):
        res = self.fetch('SELECT * FROM guilds WHERE id=?', guildId)
        if not res:
            return None
        else:
            return res["rp_token"]