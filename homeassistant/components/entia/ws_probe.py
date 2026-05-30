#!/usr/bin/env python3
"""Standalone WebSocket protocol discovery script.

Usage:
    python3 ws_probe.py <username> <password>

Run this, then physically interact with your Entia devices (flip lights,
move blinds) to capture the real-time event format. Press Ctrl+C to stop.
Delete this file once the protocol is understood.
"""

import asyncio
import json
import sys

import aiohttp
import websockets

REST_LOGIN = "https://api.entia.si/login"
WS_URL = "wss://ws.entia.si/"

LOGIN_PAYLOAD = {
    "platform": "home_assistant",
    "device_model": "home_assistant",
    "device_serial": "0000",
}


async def main(username: str, password: str) -> None:
    async with (
        aiohttp.ClientSession() as session,
        session.post(
            REST_LOGIN,
            json={"username": username, "password": password, **LOGIN_PAYLOAD},
        ) as resp,
    ):
        body = await resp.json()
        if resp.status != 200 or "token" not in body:
            print(f"Login failed ({resp.status}): {body}")
            return
        token = body["token"]

    print(f"Authenticated. Token prefix: {token[:40]}...")
    print(f"Connecting to {WS_URL}?token=... (query param auth)\n")

    try:
        async with websockets.connect(
            f"{WS_URL}?token={token}",
            ping_interval=30,
            ping_timeout=10,
        ) as ws:
            print("Connected. Interact with your devices now (Ctrl+C to stop).\n")
            async for raw in ws:
                try:
                    parsed = json.dumps(json.loads(raw), indent=2)
                except ValueError, TypeError:
                    parsed = raw
                print(f"<-- {parsed}\n")

    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed cleanly.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 ws_probe.py <username> <password>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
