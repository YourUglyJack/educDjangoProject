import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 在 Channels 中，scope 是一个字典，包含了关于当前连接的所有信息，比如 headers、path、session 等。其中，user 键通常由 Channels 的 AuthMiddlewareStack 自动添加
        self.user = self.scope['user']  # 如果用户已经登录，self.scope['user'] 就是一个 User 实例。如果用户没有登录，self.scope['user'] 就是一个 AnonymousUser 实例。
        self.id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = 'chat_%s' % self.id
        await self.channel_layer.group_add(  # self.room_group_name 和 self.channel_name 是 self.channel_layer.group_add 方法的参数
            self.room_group_name,
            self.channel_name
        )  # group_add 方法是将当前的channel 加入到 指定的group里
        await self.accept()

    async def disconnect(self, code):
        # leave room group
        await channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # receive msg from websocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        now = timezone.now()
        # send to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat(),
            }
        )

    # receive message from room group
    async def chat_message(self, event):
        # # send message to websocket, websocket 收到后就会调用 websocket.onmessage 方法 (JavaScript)
        # self.send(text_data=json.dumps({'message': message}))
        await self.send(text_data=json.dumps(event))