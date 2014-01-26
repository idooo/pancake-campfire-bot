import requests
import re
from ec2_helper import EC2Helper
from camplight import Request, Campfire
from time import sleep

# + get random cat gif (http://thecatapi.com/api/images/get?format=src&type=gif)
# + get staging status
# + chuck http://api.icndb.com/jokes/random?limitTo=[nerdy]
# help
# say random phrase
# blame somebody
# stop staging

class Bot():

    RE_URL = re.compile("<url>([^<]*)</url>", re.MULTILINE + re.IGNORECASE)
    EC2_DOWN_CODE = 80

    ec2 = None
    room = None

    def __init__(self, url, api_key, room=False, aws=False):

        self.url = url
        self.api_key = api_key

        request = Request(url, api_key)
        self.campfire = Campfire(request)

        self.account = self.campfire.account()
        self.rooms = self.campfire.rooms()

        if room:
            self.joinRoom(room)

        if aws:
            self.__awsInit(aws)

    def __awsInit(self, credentials):
        if not ('secret_key' in credentials and 'access_key' in credentials):
            return False

        self.ec2 = EC2Helper(credentials['access_key'], credentials['secret_key'])

    def __getMessages(self, messages, last_id):
        new_messages = [];
        for i in xrange(len(messages), 0, -1):
            if messages[i-1]['id'] > last_id:
                new_messages.append(messages[i-1])

        return new_messages

    def __cmdGetRandomChuckPhrase(self):
        message = "Can't connect to Chuck API =("
        params = {'limitTo': '[nerdy]'}

        r = requests.get('http://api.icndb.com/jokes/random', params=params)

        if r.status_code == 200:
            response = r.json()

            if response['type'] == 'success':
                message = response['value']['joke']

        self.room.speak(message)

    def __cmdGetRandomCatGIF(self):
        message = "Can't connect to cat API =("
        params = {'format': 'xml', 'type': 'gif'}

        r = requests.get('http://thecatapi.com/api/images/get', params=params)

        if r.status_code == 200:
            response = r.text

            res = re.search(self.RE_URL, response)
            if res:
                message = res.groups()[0]

        self.room.speak(message)

    def __cmdGetStagingStatus(self):
        is_up = False
        message = ''
        short_status = 'Staging servers status: '

        instances = self.ec2.getInstanceStatuses()
        for instance in instances:
            is_up = is_up or instance['state_code'] != self.EC2_DOWN_CODE
            message += instance['name'] + ': ' + instance['state'] + '\n'

        if is_up:
            short_status += 'RUNNING'
        else:
            short_status += 'STOPPED'

        self.room.speak(short_status)
        self.room.speak(message)

    def joinRoom(self, room):
        self.room = self.campfire.room(room)
        self.room.join()

    def start(self):

        actions = {
            '/cat': self.__cmdGetRandomCatGIF,
            '/staging': self.__cmdGetStagingStatus,
            '/chuck': self.__cmdGetRandomChuckPhrase
        }

        msgs = self.room.recent();
        last_id = msgs[-1]['id'];

        while True:

            print '.'

            msgs = self.room.recent();
            messages = self.__getMessages(msgs, last_id)

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
