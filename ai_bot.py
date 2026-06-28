#!/usr/bin/env python3
"""
SimpleX AI Bot – a privacy-respecting AI assistant powered by Groq.

Requirements:
    pip install websockets groq

Usage:
    1. Start simplex-chat as a WebSocket server:
       simplex-chat -p 5225
    2. Enable auto-accept and get your address:
       /auto_accept on
       /address        (copy this address)
    3. Set your Groq API key:
       export GROQ_API_KEY="gsk_..."
    4. Run the bot:
       python ai_bot.py
    5. Connect your SimpleX app and start chatting.
       Use /reset to clear your conversation history.
"""

import asyncio
import json
import logging
import os
import uuid

import websockets
from groq import AsyncGroq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_bot")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful, friendly AI assistant on SimpleX Chat. "
    "Keep answers concise and respectful of user privacy. "
    "If you don't know something, say so honestly."
)


class AIBot:
    def __init__(self, port=5225):
        self.uri = f"ws://localhost:{port}"
        self.history = {}          # contact_name -> list of messages
        self._last_sent = {}       # contact_name -> text of most recent sent message

    async def run(self):
        async with websockets.connect(self.uri) as ws:
            logger.info("AI Bot connected. Waiting for messages...")
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    resp = data.get("resp", {})
                    if resp.get("type") != "newChatItems":
                        continue

                    for item in resp.get("chatItems", []):
                        chat = item.get("chatItem", {})
                        if chat.get("sent"):
                            continue

                        text = (
                            chat.get("content", {})
                            .get("msgContent", {})
                            .get("text", "")
                        )
                        if not text:
                            continue

                        contact = item.get("chatInfo", {}).get("contact", {})
                        name = (
                            contact.get("localDisplayName")
                            or contact.get("displayName")
                            or ""
                        )
                        if not name:
                            continue

                        # ---------- anti‑loop guard ----------
                        # If this incoming message is exactly the last thing we sent
                        # to this contact, it's an echo of our own reply → skip it.
                        if self._last_sent.get(name) == text:
                            logger.debug("Skipping own echo for %s", name)
                            continue

                        logger.info("Received from %s: %s", name, text)

                        # Handle /reset command
                        if text.strip().lower() == "/reset":
                            self.history.pop(name, None)
                            self._last_sent.pop(name, None)
                            await self._send(ws, name, "Conversation history cleared.")
                            continue

                        # Maintain per-contact history
                        if name not in self.history:
                            self.history[name] = []
                        self.history[name].append({"role": "user", "content": text})

                        # Build conversation
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                        messages += self.history[name][-20:]  # last 20 messages

                        try:
                            response = await groq_client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=messages,
                                temperature=0.7,
                                max_tokens=500,
                            )
                            reply = response.choices[0].message.content.strip()
                        except Exception as e:
                            logger.exception("Groq API error")
                            reply = "Sorry, I'm having trouble thinking right now. Try again later."

                        self.history[name].append({"role": "assistant", "content": reply})
                        await self._send(ws, name, reply)
                        # remember what we just sent to block its echo
                        self._last_sent[name] = reply

                except Exception:
                    logger.exception("Error processing message")

    async def _send(self, ws, contact_name: str, text: str):
        cmd = f"@{contact_name} {text}"
        await ws.send(json.dumps({"corrId": str(uuid.uuid4()), "cmd": cmd}))
        logger.info("Sent to %s: %s", contact_name, text)


if __name__ == "__main__":
    asyncio.run(AIBot().run())