from channels.generic.websocket import AsyncWebsocketConsumer
import json

class BaseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def disconnect(self, close_code):
        pass
    
    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))