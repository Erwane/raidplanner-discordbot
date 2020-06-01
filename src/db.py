# -*- coding: utf-8 -*-

import os, json, sqlite3, time
from pprint import pprint

class Db:
    def __init__(self, bot):
        self.bot = bot
        dbPath = bot.config['rootPath'] + '/resources/bot.db'
        self.db = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

        self._doMigrations()

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
            result = c.fetchone()

            if not result:
                return False

            output = dict(result)

            if 'response' in output:
                output['infos'] = json.loads(output['response'])

            return output
        except Exception as e:
            return False

    # fetch all
    def fetchall(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            result = c.fetchall()

            if not result:
                return False

            output = list()
            for row in result:
                item = dict(row)
                if 'response' in item:
                    item['infos'] = json.loads(item['response'])

                output.append(item)

            return output
        except Exception as e:
            return False

    # column Exists
    def columnExists(self, table, name):
        try:
            c = self.db.cursor()
            c.execute("PRAGMA table_info('" + table + "')")
            rows = c.fetchall()

            for column in rows:
                if column['name'] == name:
                    return True

            return False
        except Exception as e:
            return False

    # execute query
    def query(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            self.db.commit()
        except Exception as e:
            raise e

    """
    Detach bot, delete all informations
    """
    def detachBot(self, discordGuildId):
        self.query('DELETE FROM events WHERE guild_id=?', discordGuildId)
        self.query('DELETE FROM guilds WHERE id=?', discordGuildId)

    # get guild from DB or API if don't exists
    def getGuild(self, discordGuildId, raidplannerToken=False):
        if not raidplannerToken:
            guild = self.fetch("SELECT * FROM guilds WHERE id=?", discordGuildId)
        else:
            guild = self.fetch("SELECT * FROM guilds WHERE rp_token=?", raidplannerToken)

            if not guild or guild['expire'] < int(time.time()):
                fromApi = self.bot.api.getGuild(raidplannerToken)

                # No guild with this token, return false
                if not fromApi:
                    return False

                # store api result
                expire = int(time.time()) + (3600 * 24 * 7)
                if not guild:
                    self.query('INSERT INTO guilds (id, rp_token, response, expire) VALUES(?, ?, ?, ?)',
                        discordGuildId, raidplannerToken, json.dumps(fromApi['response']), expire
                    )
                else:
                    self.query('UPDATE guilds SET rp_token=?, response=?, expire=? WHERE id=?',
                        raidplannerToken, json.dumps(fromApi['response']), expire, discordGuildId
                    )

            # redo currentValue after api update
            guild = self.fetch("SELECT * FROM guilds WHERE id=?", discordGuildId)

        return guild

    # get raidplanner guild token
    def getTokenGuild(self, guildId):
        res = self.fetch('SELECT * FROM guilds WHERE id=?', guildId)
        if not res:
            return False
        else:
            return res["rp_token"]

    # get raidplanner user
    # return False if not linked
    def getUser(self, discordUserId):
        user = self.fetch("SELECT * FROM users WHERE id=?", discordUserId)

        if not user or user['expire'] < int(time.time()):
            # from api
            fromApi = self.bot.api.getUser(discordUserId)

            # nothing exists
            if not fromApi:
                self.query('DELETE FROM users WHERE id=?', discordUserId)
                return False

            # store api result
            expire = int(time.time()) + (3600 * 24 * 7)
            if not user:
                self.query('INSERT INTO users (id, rp_id, response, expire) VALUES(?, ?, ?, ?)',
                    discordUserId, fromApi['rp_id'], json.dumps(fromApi['response']), expire
                )
            else:
                self.query('UPDATE users SET rp_id=?, response=?, expire=? WHERE id=?',
                    fromApi['rp_id'], json.dumps(fromApi['response']), expire, discordUserId
                )

            # redo currentValue after api update
            user = self.fetch("SELECT * FROM users WHERE id=?", discordUserId)

        return user

    """
    DB migrations
    """
    def _doMigrations(self):
        self.createTable("""users ("id" PK INTEGER NOT NULL, "rp_id" INTEGER, "response" TEXT, "expire" INTEGER)""")
        self.createTable("""guilds ("id" PK INTEGER NOT NULL, "rp_token" TEXT, "response" TEXT, "channel" INTEGER, "expire" INTEGER)""")
        self.createTable("""events ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "guild_id" INTEGER NOT NULL, "event_id" INTEGER NOT NULL, "msg_id" INTEGER NOT NULL, "modified" INTEGER, "event_start" INTEGER)""")

        # age maximum des events
        if not self.columnExists('guilds', 'event_days'):
            self.query('ALTER TABLE guilds ADD COLUMN "event_days" INTEGER NOT NULL DEFAULT 7')
