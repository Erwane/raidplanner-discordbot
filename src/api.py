# -*- coding: utf-8 -*-

from .mylibs import log
from datetime import datetime
from requests.structures import CaseInsensitiveDict
import random
import hmac
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import urllib
import discord
from pprint import pprint

class Api:
    def __init__(self, bot):
        # self.client = http.client
        self.config = bot.config['api']
        self.baseUrl = self.config['base_url']
        self.bot = bot
        log().info(f"Api initiliazed with baseUrl: {self.baseUrl}")

    def doRequest(self, method, uri, params={}, headers={}):
        try:
            headers['content-type'] = 'application/json'
            params = json.dumps(params, separators=(',', ':'))

            log().debug(f"Api::{method} - url={uri}; headers={headers}; data={params}")

            if method == 'GET':
                headers = self._appendSignature(headers)
                request = Request(
                    self.config['base_url'] + uri,
                    method=method,
                    headers=headers
                )
            else:
                headers = self._appendSignature(headers, params)
                request = Request(
                    self.config['base_url'] + uri,
                    method=method,
                    headers=headers,
                    data=params.encode('utf-8')
                )


            response = urlopen(request)

            if response and response.status >=200 and response.status < 300:
                return json.loads(response.read())
            else:
                return False

        except HTTPError as e:
            body = e.read()
            if e.code < 500:
                return json.loads(body)
            else:
                log().warning(f"Api::{method} - uri={uri}; code={e.code}; body={body}")
                return False

        except Exception as e:
            log().error(f"Api::{method} - uri={uri}; file={e.filename}; exception={str(e)}")
            return False

    # GET request.
    def _get(self, uri, headers={}):
        return self.doRequest("GET", uri, headers=headers)

    # PUT request
    def _put(self, uri, params={}, headers={}):
        return self.doRequest("PUT", uri, params=params, headers=headers)

    # DELETE request
    def _delete(self, uri, params={}, headers={}):
        return self.doRequest("DELETE", uri, params=params, headers=headers)

    # get Raidplanner User information
    def getUser(self, discordUserId):
        user = False

        response = self._get('/connections/discord/%d' % int(discordUserId))
        if response != False:
            user = {
                'rp_id': response["id"],
                'response': response,
            }

        return user

    # get Guild
    def getGuild(self, token):
        guild = False

        response = self._get('/guilds/discord/%s' % urllib.parse.quote_plus(token))
        if response != False:
            guild = {
                'rp_token': token,
                'response': response,
            }

        return guild

    # Attach discord server to guild
    def discordAttach(self, author, discordGuild, raidplannerGuild):
        self._discordAttachDetach('PUT', author, discordGuild, raidplannerGuild)

    # Detach discord server to guild
    def discordDetach(self, author, discordGuild, raidplannerGuild):
        self._discordAttachDetach('DELETE', author, discordGuild, raidplannerGuild)

    def _discordAttachDetach(self, method, author, discordGuild, raidplannerGuild):
        guildId = raidplannerGuild['infos']['id']

        authorId = 0
        discordGuildId = 0
        discordGuildName = ''

        if isinstance(author, discord.Member):
            authorId = author.id

        if isinstance(discordGuild, discord.Guild):
            discordGuildId = discordGuild.id
            discordGuildName = discordGuild.name

        response = self.doRequest(method, f'/guild/{guildId}/discord', {
            'server_id': discordGuildId,
            'server_name': discordGuildName,
            'author_id': authorId
        }, {'discord-token': str(raidplannerGuild['rp_token']), 'headers': 'date discord-token'})

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

    def setPresence(self, eventId, userId, newStatus, guildId):
        try:
            # get token guild
            guildToken = self.bot.db.getTokenGuild(guildId)
            # set presence via api
            response = self._put(f'/events/{eventId}/presence/{userId}', {
                'status': newStatus
            }, {'discord-token': str(guildToken), 'headers': 'date discord-token'})
            # log
            log().debug(f"Api::setPresence: guild={guildId}, event={eventId}; user={userId}; status={newStatus}")

            return response
        except Exception as e:
            log().error(f"Api::setPresence: uri=/events/{eventId}/presence/{userId}; exception={str(e)}")
            return False

    def _appendSignature(self, headers={}, params={}):
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
        # body params
        if len(params) > 0:
            toSign.append(params)

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
