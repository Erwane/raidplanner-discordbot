
from .db import Db
from .mylibs import log
import datetime
import http.client
import json
import time
import urllib

class Api:
    def __init__(self, config):
        self.client = http.client
        self.baseUrl = config['api_base_url']
        self.db = Db(self)
        log().info(f"Api initiliazed with baseUrl: {self.baseUrl}")

    def _get(self, uri):
        try:
            log().info(f"Api Get: {self.baseUrl}{uri}")
            connection = self.client.HTTPConnection(self.baseUrl, timeout=2)
            connection.request("GET", uri)

            return connection.getresponse()
        except Exception as e:
            log().warning(f"Api Get: {str(e)}")
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
                self.db.query('INSERT INTO users (id, rp_id, response, expire) VALUES(?, ?, ?, ?)', me['id'], me['rp_id'], json.dumps(me['response']), me['expire'])
            else:
                self.db.query('UPDATE users SET rp_id=?, response=?, expire=? WHERE id=?', me['rp_id'], json.dumps(me['response']), me['expire'], me['id'])

            return me

    # get Guild
    def getGuild(self, token):
        guild = None

        response = self._get('/guilds/discord/%s' % urllib.parse.quote_plus(token))

        # have response and status code is 200
        if response and response.status >=200 and response.status < 300:
            guild = {
                'rp_token': token,
                'response': json.loads(response.read()),
            }

        return guild

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
