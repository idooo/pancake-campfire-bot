from camplight import Request, Campfire
from time import sleep

# get random cat gif (http://thecatapi.com/api/images/get?format=src&type=gif)
# say random phrase
# get staging status
# blame somebody

class Bot():

    def __init__(self, url, api_key, room=False):

        self.url = url
        self.api_key = api_key

        request = Request(url, api_key)
        self.campfire = Campfire(request)

        self.account = self.campfire.account()
        self.rooms = self.campfire.rooms()
        self.room = ''

        print self.rooms

        if room:
            self.joinRoom(room)

    def joinRoom(self, room):
        self.room = room
        room = self.campfire.room(room)
        room.join()

    def getMessages(self, messages, last_id):
        new_messages = [];
        for i in xrange(len(messages), 0, -1):
            if messages[i-1]['id'] > last_id:
                new_messages.append(messages[i-1])

        return new_messages

    def start(self):

        msgs = self.room.recent();
        last_id = msgs[-1]['id'];

        while True:

            print 'check'

            msgs = self.room.recent();
            messages = self.getMessages(msgs, last_id)

            if messages:
                last_id = msgs[-1]['id'];

            command = None
            for message in messages:
                if message['body'] and '/clear' in message['body']:
                    command = 'clear'

            if command:
                if command == 'clear':
                    for i in range(0,10):
                        self.room.speak('.')

                    print 'command', command

            sleep(2);
