import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')

from django.core.asgi import get_asgi_application

# Initialize Django app registry BEFORE importing anything that touches models
django_asgi_app = get_asgi_application()

# These imports must come AFTER get_asgi_application() so the app registry is ready
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import tasks.routing
from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(
                    tasks.routing.websocket_urlpatterns
                )
            )
        )
    ),
})
