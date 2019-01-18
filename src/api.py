from .db import Db
import http.client
import json
import time

class Api:
    def __init__(self):
        self.client = http.client
        self.baseUrl = '192.168.33.1:3000'
        self.db = Db()

    def _get(self, uri):
        try:
            print(f"Api GET: {uri}")
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

    #
    def _userFromApi(self, id, fromDb):
        response = self._get('/connections/discord/%d' % id)

        if 'code' in response and response['code'] >= 300:
            print("not connected")

            return None
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


    def events(self, id):
        return None

