# -*- coding: utf-8 -*-

from .db import Db
from .mylibs import log
from datetime import datetime
from requests.structures import CaseInsensitiveDict
import random
import hmac
import http.client
import json
import urllib

class Api:
    def __init__(self, config):
        self.client = http.client
        self.config = config['api']
        self.baseUrl = self.config['base_url']
        self.db = Db(self)
        log().info(f"Api initiliazed with baseUrl: {self.baseUrl}")

    def _get(self, uri, headers={}):
        try:
            headers = self._appendSignature(headers)

            # connection
            # log().info(f"Api Get: {self.baseUrl}{uri}")
            connection = self.client.HTTPConnection(self.baseUrl, timeout=2)
            connection.request("GET", uri, headers=headers)

            response = connection.getresponse()

            if response and response.status >=200 and response.status < 300:
                return json.loads(response.read())
            else:
                log().info(f"Api._get: uri={uri}; status={response.status}; response={response.read()}")
                return False

        except Exception as e:
            log().warning(f"Api._get: uri={uri}; exception={str(e)}")
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
                event['date_start'] = datetime.strptime(event['date_start'], "%Y-%m-%dT%H:%M:%S%z")
                event['date_start_timestamp'] = event['date_start'].timestamp()
                # format modified
                event['modified'] = datetime.strptime(event['modified'], "%Y-%m-%dT%H:%M:%S%z")
                event['modified_timestamp'] = event['modified'].timestamp()

                # append to events
                events.append(event)

        return events

    def _appendSignature(self, headers):
        headers = CaseInsensitiveDict(headers)

        if not 'date' in headers:
            headers['date'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00');

        if not 'headers' in headers:
            headers['headers'] = "date"

        # nonce
        nonce = random.randrange(100000, 999999)

        toSign = []
        # headers content
        for name in headers['headers'].split(' '):
            toSign.append(headers[name])
        # nonce
        toSign.append(nonce)

        # create hmac
        content = json.dumps(toSign, separators=(',', ':')).encode('utf-8')
        digest = hmac.new(self.config['secret'].encode('utf-8'), msg=content, digestmod='sha256')

        signatureTemplate = 'keyId="{0}",algorithm="hmac-sha256",headers="{1}",nonce="{2}",signature="{3}"'
        signature = signatureTemplate.format(
            self.config['key'],
            headers['headers'],
            nonce,
            digest.hexdigest().upper()
        )

        headers['signature'] = signature

        return headers