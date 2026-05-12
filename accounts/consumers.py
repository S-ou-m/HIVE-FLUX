import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FacultyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"faculty_{self.user.id}"
            # Join faculty group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Leave faculty group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from room group
    async def faculty_event(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event["message"]))

    # Generic handler for any message type we want to broadcast
    async def broadcast_update(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

class AttendanceConsumer(AsyncWebsocketConsumer):
    """ Live telemetry for specific attendance sessions """
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f"attendance_{self.session_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def attendance_update(self, event):
        """ Handles real-time check-in signals """
        await self.send(text_data=json.dumps(event['payload']))
