
from .db import Db
from .mylibs import log
import datetime as dt
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

            response = connection.getresponse()

            if response and response.status >=200 and response.status < 300:
                return json.loads(response.read())
            else:
                log().info(f"Api Get: uri={uri}; status={response.status}; response={response.read()}")
                return False

        except Exception as e:
            log().warning(f"Api Get: uri={uri}; exception={str(e)}")
            return False

    # get Raidplanner User information
    def getUser(self, userId):
        user = None

        response = self._get('/connections/discord/%d' % int(userId))
        if response != False:
            user = {
                'rp_id': response["id"],
                'response': response,
            }

        return user

    # get Guild
    def getGuild(self, token):
        guild = None

        response = self._get('/guilds/discord/%s' % urllib.parse.quote_plus(token))
        if response != False:
            guild = {
                'rp_token': token,
                'response': response,
            }

        return guild

    """
    fetch next raidplanner events
    """
    def nextEvents(self):
        events = []

        response = self._get('/events/discord')
        if response != False:
            for event in response:
                # format date start
                event['date_start'] = dt.datetime.strptime(event['date_start'], "%Y-%m-%dT%H:%M:%S%z")
                event['date_start_timestamp'] = event['date_start'].timestamp()
                # format modified
                event['modified'] = dt.datetime.strptime(event['modified'], "%Y-%m-%dT%H:%M:%S%z")
                event['modified_timestamp'] = event['modified'].timestamp()

                # append to events
                events.append(event)

        return events
