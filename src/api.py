
from .db import Db
import datetime
import http.client
import json
import time
import urllib
from .mylibs import log

class Api:
    def __init__(self):
        self.client = http.client
        self.baseUrl = '192.168.33.1:3000'
        self.db = Db()

    def _get(self, uri):
        try:
            log().info(f"Api GET: {uri}")
            connection = self.client.HTTPConnection(self.baseUrl)
            connection.request("GET", uri)
            response = connection.getresponse()

            return json.loads(response.read())
        except Exception as e:
            return None

    # get Raidplanner User information from local db or API
    # return user dict
    def user(self, id):
        # from db
        item = self.db.fetch('SELECT * FROM users WHERE id=?', id)
        if not item or item['expire'] < time.time():
            user = self._userFromApi(id, item)
        else:
            user = {
                'id': item['id'],
                'rp_id': item['rp_id'],
                'response': json.loads(item['response']),
                'expire': item['expire']
            }

        return user

    # get Raidplanner Guild information from local db or API
    # return user dict
    def guild(self, id, token=None):
        guild = None

        # from db
        if token:
            res = self.db.fetch('SELECT * FROM guilds WHERE rp_token=?', token)
            if not res or res['expire'] < time.time():
                guild = self._guildFromApi(id, token)

        elif id:
            res = self.db.fetch('SELECT * FROM guilds WHERE id=?', id)
            # guild unknown, return empty object
            if not res:
                return None

        if not guild and res:
            guild = {
                'id': res['id'],
                'rp_token': res['rp_token'],
                'response': json.loads(res['response']),
                'expire': res['expire']
            }

        return guild

    # user from API
    def _userFromApi(self, id, fromDb):
        response = self._get('/connections/discord/%d' % id)

        if 'code' in response and response['code'] >= 300:
            return False
        else:
            me = {
                'id': id,
                'rp_id': response['id'],
                'response': response,
                'expire': int(time.time()) + (3600 * 6)
            }

            if not fromDb:
                self.db.insert('INSERT INTO users (id, rp_id, response, expire) VALUES(?, ?, ?, ?)', me['id'], me['rp_id'], json.dumps(me['response']), me['expire'])
            else:
                self.db.update('UPDATE users SET rp_id=?, response=?, expire=? WHERE id=?', me['rp_id'], json.dumps(me['response']), me['expire'], me['id'])

            return me

    # Guild from API
    def _guildFromApi(self, id, token):
        response = self._get('/guilds/discord/%s' % urllib.parse.quote_plus(token))

        if not response or ('code' in response and response['code'] >= 300):
            return False
        else:
            item = {
                'id': id,
                'rp_token': token,
                'response': response,
                'expire': int(time.time()) + (3600 * 6)
            }

            res = self.db.fetch('SELECT * FROM guilds WHERE id=?', id)

            if not res:
                self.db.insert('INSERT INTO guilds (id, rp_token, response, expire) VALUES(?, ?, ?, ?)', id, item['rp_token'], json.dumps(item['response']), item['expire'])
            else:
                self.db.update('UPDATE guilds SET rp_token=?, response=?, expire=? WHERE id=?', item['rp_token'], json.dumps(item['response']), item['expire'], id)

            return item

    """
    fetch next raidplanner events
    """
    def nextEvents(self):
        response = self._get('/events/discord')

        events = []
        if response and not ('code' in response and response['code'] >= 300):
            for event in response:
                # format date start
                event['date_start'] = datetime.datetime.strptime(event['date_start'], "%Y-%m-%dT%H:%M:%S%z")
                event['date_start_timestamp'] = event['date_start'].timestamp()
                # format modified
                event['modified'] = datetime.datetime.strptime(event['modified'], "%Y-%m-%dT%H:%M:%S%z")
                event['modified_timestamp'] = event['modified'].timestamp()

                # append to events
                events.append(event)

        return events
