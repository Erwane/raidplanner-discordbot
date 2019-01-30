# -*- coding: utf-8 -*-
import sqlite3
import os

class Db:
    def __init__(self):
        dbPath = os.getcwd() + '/resources/bot.db'
        self.db = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

        self.createTable("""users ("id" PK INTEGER NOT NULL, "rp_id" INTEGER, "response" TEXT, "expire" INTEGER)""")
        self.createTable("""guilds ("id" PK INTEGER NOT NULL, "rp_token" TEXT, "response" TEXT, "channel" INTEGER, "expire" INTEGER)""")

    def __del__(self):
        self.db.close()

    def createTable(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS %s" % query)
            self.db.commit()
        except Exception as e:
            raise e

    def fetch(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            return c.fetchone()
        except Exception as e:
            raise e

    def insert(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            self.db.commit()
        except Exception as e:
            raise e

    def update(self, query, *args):
        try:
            c = self.db.cursor()
            c.execute(query, args)
            self.db.commit()
        except Exception as e:
            raise e


