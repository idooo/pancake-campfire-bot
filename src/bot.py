import requests
import re
import random
from ec2_helper import EC2Helper
from camplight import Request, Campfire
from time import sleep

# + get random cat gif (http://thecatapi.com/api/images/get?format=src&type=gif)
# + get staging status
# + chuck http://api.icndb.com/jokes/random?limitTo=[nerdy]
# + help
# roll
# say random phrase
# + blame somebody
# stop staging

class Bot():

    RE_URL = re.compile("<url>([^<]*)</url>", re.MULTILINE + re.IGNORECASE)
    EC2_DOWN_CODE = 80

    ec2 = None
    rooms = None
    joined_rooms = {}
    actions = {}
    user = {}

    def __init__(self, url, api_key, rooms=False, aws=False):

        self.url = url
        self.api_key = api_key

        request = Request(url, api_key)
        self.campfire = Campfire(request)

        self.account = self.campfire.account()
        self.available_rooms = self.campfire.rooms()

        self.user = self.campfire.user()

        if rooms:
            self.joinRooms(rooms)

        if aws:
            self.__awsInit(aws)

        self.__setActions()

    def __setActions(self):

        self.actions = {
            '/help': {
                'action': self.__cmdHelp,
                'help': 'Show this help'
            },
            '/cat': {
                'action': self.__cmdGetRandomCatGIF,
                'help': 'Post random cat gif'
            },
            '/staging': {
                'action': self.__cmdGetStagingStatus,
                'help': 'Get staging servers status'
            },
            '/chuck': {
                'action': self.__cmdGetRandomChuckPhrase,
                'help': 'Post random Chuck\'s phrase'
            },
            '/blame': {
                'action': self.__cmdBlameSomebody,
                'help': 'Blame somebody'
            }
        }

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

    def __cmdHelp(self, room):
        message = 'Pancake bot, here are available commands:\n'
        for action_name in self.actions.keys():
            message += action_name
            if 'help' in self.actions[action_name]:
                message += ' - ' + self.actions[action_name]['help']
            message += '\n'

        room.speak(message)

    def __cmdGetRandomChuckPhrase(self, room):
        message = "Can't connect to Chuck API =("
        params = {'limitTo': '[nerdy]'}

        r = requests.get('http://api.icndb.com/jokes/random', params=params)

        if r.status_code == 200:
            response = r.json()

            if response['type'] == 'success':
                message = response['value']['joke']

        room.speak(message)

    def __cmdGetRandomCatGIF(self, room):
        message = "Can't connect to cat API =("
        params = {'format': 'xml', 'type': 'gif'}

        r = requests.get('http://thecatapi.com/api/images/get', params=params)

        if r.status_code == 200:
            response = r.text

            res = re.search(self.RE_URL, response)
            if res:
                message = res.groups()[0]

        room.speak(message)

    def __cmdGetStagingStatus(self, room):

        if not self.ec2:
            room.speak('Can\'t connect to AWS API =(')
            return False

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

        room.speak(short_status)
        room.speak(message)

    def __cmdBlameSomebody(self, room):
        message = '{}, this is your fault!'

        users = room.status()['users']
        usernames = []
        for user in users:
            if user['name'] != self.user['name']:
                usernames.append(user['name'])

        username = random.choice(usernames)

        room.speak(message.format(username))

    def joinRooms(self, rooms):
        self.rooms = rooms.split(',')
        for room in self.rooms:
            self.joinRoom(room)

    def joinRoom(self, room):
        self.joined_rooms.update({room: self.campfire.room(room)})
        self.joined_rooms[room].join()

    def start(self):

        last_ids = {}
        for room_name in self.joined_rooms:
            msgs = self.joined_rooms[room_name].recent();
            last_ids.update({room_name: msgs[-1]['id']});

        while True:

            print '.'

            for room in self.joined_rooms:

                msgs = self.joined_rooms[room].recent();
                messages = self.__getMessages(msgs, last_ids[room])

                if messages:
                    last_ids[room] = msgs[-1]['id'];

                command = None
                for message in messages:
                    if message['body'] and message['user_id'] != self.user['id']:
                        for action_name in self.actions:
                            if action_name in message['body']:
                                self.actions[action_name]['action'](self.joined_rooms[room])

                if command:
                    print 'command', command

            sleep(2)
