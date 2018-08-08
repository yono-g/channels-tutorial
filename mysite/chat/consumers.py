from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # どのコンシューマもscopeを持つ。これにはURLに関する情報と、認証ユーザに関する情報が含まれる
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        # WebsocketConsumerは同期コンシューマであるが、channel_layer以下のメソッドはすべて非同期関数であるため、async_to_syncラッパーが必要。
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # Websocket接続を受け入れる。これがconnect内で呼ばれないと接続は拒否となる。
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from Websocket
    # ユーザーが入力したメッセージはWebsocket経由でコンシューマが受け取る。
    # 同じroom_groupのインスタンスにメッセージを転送する。
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',  # typeキーは特殊なキーで、イベントを受け取ったコンシューマはこのキーの名前のメソッドを呼び出す。
                'message': message
            }
        )

    # Receive message from room group
    # コンシューマは、別のコンシューマから転送されてきたメッセージを受け取って、Websocket経由でブラウザに返す
    def chat_message(self, event):
        message = event['message']

        # Send message to Websocket
        self.send(text_data=json.dumps({
            'message': message
        }))
