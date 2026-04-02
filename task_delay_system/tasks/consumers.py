import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # A specific group for this exact user
        self.user_group_name = f"user_{self.user.id}"
        
        # A global group for managers
        self.manager_group_name = "managers"

        # Join the user's personal exact group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Check if they are a manager, and join the broadcast group if so
        # Because we are in async, we can't do direct ORM calls easily without sync_to_async
        # We can check the property `is_manager`. Since `groups.all()` is a DB call,
        # we need to be careful. The simplest approach for a university project is checking
        # sync_to_async wrapper.
        from asgiref.sync import sync_to_async
        
        @sync_to_async
        def get_is_manager(user):
            return user.is_manager
            
        is_manager = await get_is_manager(self.user)
        
        if is_manager:
            await self.channel_layer.group_add(
                self.manager_group_name,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code):
        if not hasattr(self, 'user') or self.user.is_anonymous:
            return
            
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        
        from asgiref.sync import sync_to_async
        @sync_to_async
        def get_is_manager(user):
            return user.is_manager
            
        is_manager = await get_is_manager(self.user)
        
        if is_manager:
            await self.channel_layer.group_discard(
                self.manager_group_name,
                self.channel_name
            )

    # Receive message from room group
    async def send_notification(self, event):
        message = event["message"]
        title = event.get("title", "Notification")
        type = event.get("type_alert", "info")

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "title": title,
            "type": type
        }))
