from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TelemetriConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("telemetri", self.channel_name)
        await self.accept()
        print("Dashboard baglandi")

    async def disconnect(self, code):
        await self.channel_layer.group_discard("telemetri", self.channel_name)

    async def telemetri_mesaj(self, event):
        await self.send(text_data=json.dumps(event['data']))