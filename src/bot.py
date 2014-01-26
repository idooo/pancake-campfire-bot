import requests
import re
from camplight import Request, Campfire
from time import sleep

# get random cat gif (http://thecatapi.com/api/images/get?format=src&type=gif)
# say random phrase
# get staging status
# blame somebody

class Bot():

    RE_URL = re.compile("<url>([^<]*)</url>", re.MULTILINE + re.IGNORECASE)

    def __init__(self, url, api_key, room=False):

        self.url = url
        self.api_key = api_key

        request = Request(url, api_key)
        self.campfire = Campfire(request)

        self.account = self.campfire.account()
        self.rooms = self.campfire.rooms()
        self.room = None

        if room:
            self.joinRoom(room)

    def _getMessages(self, messages, last_id):
        new_messages = [];
        for i in xrange(len(messages), 0, -1):
            if messages[i-1]['id'] > last_id:
                new_messages.append(messages[i-1])

        return new_messages

    def _cmdGetRandomCatGIF(self):
        message = "Can't connect to cat API =("
        params = {'format': 'xml', 'type': 'gif'}

        r = requests.get('http://thecatapi.com/api/images/get', params=params)

        if r.status_code == 200:
            response = r.text

            res = re.search(self.RE_URL, response)
            if res:
                message = res.groups()[0]

        self.room.speak(message)

    def joinRoom(self, room):
        self.room = self.campfire.room(room)
        self.room.join()

    def start(self):

        actions = {
            '/cat': self._cmdGetRandomCatGIF
        }

        msgs = self.room.recent();
        last_id = msgs[-1]['id'];

        while True:

            print '.'

            msgs = self.room.recent();
            messages = self._getMessages(msgs, last_id)

            if messages:
                last_id = msgs[-1]['id'];

            command = None
            for message in messages:
                if message['body']:

                    for action_name in actions:
                        if action_name in message['body']:
                            actions[action_name]()

            if command:
                print 'command', command

            sleep(2);
