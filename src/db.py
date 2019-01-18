# -*- coding: utf-8 -*-
import sqlite3
import os

class Db:
    def __init__(self):
        dbPath = os.getcwd() + '/resources/bot.db'
        self.db = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

    def __del__(self):
        self.db.close()

    def fetch(self, query, *args):
        c = self.db.cursor()

        c.execute(query, args)

        return c.fetchone()

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


