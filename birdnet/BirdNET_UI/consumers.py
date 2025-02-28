from channels.generic.websocket import AsyncWebsocketConsumer
import json

test_message = {
                    "type": "send_bird_update",
                    "data": {
                        "update": "unknown!!!!!!!!!"
                    }
                }
topic = "birds"

class BirdConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("BirdConsumer connected to group: birds")
        await self.channel_layer.group_add("birds", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("birds", self.channel_name)

    async def receive(self, text_data):
        # print("BirdConsumer received message:", text_data)
        # Parse the incoming message
        try:
            data = json.loads(text_data)
            # Ensure data is a dictionary
            if isinstance(data, dict):
                # Broadcast the message to all clients in the group
                await self.channel_layer.group_send(
                    "birds",
                    {
                        "type": "send_bird_update",
                        "data": data  # Ensure this is a dictionary
                    }
                )
            else:
                print("Received data is not a dictionary:", data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    # async def send(self, text_data=None, bytes_data=None):
    #     print("BirdConsumer sending message to channel layer", text_data)
    #     await super().send(text_data=text_data, bytes_data=bytes_data)  

        # await self.channel_layer.group_send(
        #     "birds",
        #     json.loads(text_data)
        # )

    async def send_bird_update(self, event):
        # print("BirdConsumer received event: send_bird_update")
        data = event['data']
        # print("Sending bird update to WebSocket:", data)
        await self.send(text_data=json.dumps(data))
