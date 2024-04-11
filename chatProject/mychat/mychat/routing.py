from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing

# ProtocolTypeRouter 是 Django Channels 中的一个路由分发器，用于根据连接的类型来将连接路由到指定的应用程序。这允许 Django Channels 同时处理 HTTP 和 WebSocket 连接，或者其他任何 ASGI 协议的连接。
# 当一个新的连接打开时，ProtocolTypeRouter 会查看连接的类型（例如 "http" 或 "websocket"），然后将其路由到对应的应用程序。这些应用程序可以是任何符合 ASGI 规范的应用程序，包括 Django Channels 的 URLRouter，或者任何其他 ASGI 应用

# todo Django 3.2.7 版本必须与 channel 2.4.0 版本配合，否则无法启动ASGI服务器，我也不知道为什么

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(  # 每次 WebSocket 连接时，AuthMiddlewareStack 就会自动处理用户认证，并将用户信息添加到 scope 中
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})