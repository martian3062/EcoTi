"""Channels WebSocket consumer — streams the live fused-event feed + toasts."""
from __future__ import annotations

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from core.bus import FEED_GROUP


class FeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(FEED_GROUP, self.channel_name)
        await self.accept()
        await self.send(json.dumps({"kind": "hello", "data": {"msg": "EcoTi feed connected"}}))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(FEED_GROUP, self.channel_name)

    async def feed_event(self, message):
        """Handler for messages sent to the group with type 'feed.event'."""
        await self.send(json.dumps({"kind": message["kind"], "data": message["data"]}))
