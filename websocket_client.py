#!/usr/bin/env python3
"""
websocket_client.py

This module implements the WebSocketClient class that connects to Binance's WebSocket API,
listens for real-time ticker data, and updates a shared in-memory dictionary with the latest prices.

ARNAV'S SUMMARY: This module contains the WebSocketClient class that connects to Binance’s combined WebSocket endpoint,
subscribes to ticker updates for the provided symbols, and updates the shared latest_prices dictionary.
"""

import asyncio
import json
import time
import websockets  # Ensure you have installed websockets==10.4 via requirements.txt

class WebSocketClient:
    def __init__(self, symbols, latest_prices):
        """
        Initialize the WebSocket client.
        
        Args:
            symbols (list): List of symbols (strings) to subscribe to (e.g., ["btcusdt", "ethusdt"]).
            latest_prices (dict): Shared dictionary to update with latest price data.
        """
        self.symbols = symbols
        self.latest_prices = latest_prices
        self.base_url = "wss://stream.binance.com:9443/stream?streams="
        # Create a combined stream string: e.g., "btcusdt@ticker/ethusdt@ticker/..."
        self.streams = "/".join([f"{symbol}@ticker" for symbol in symbols])
        self.ws_url = self.base_url + self.streams

    async def connect_and_listen(self):
        """
        Connect to Binance WebSocket and continuously listen for ticker messages.
        Implements automatic reconnection in case of errors.
        """
        while True:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,   # Send periodic pings to keep the connection alive
                    ping_timeout=20
                ) as websocket:
                    print(f"[WebSocket] Connected to {self.ws_url}")
                    # Listen indefinitely for incoming messages
                    async for message in websocket:
                        await self.handle_message(message)
            except Exception as e:
                # Log the error and wait a few seconds before reconnecting.
                print(f"[WebSocket] Connection error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def handle_message(self, message):
        """
        Process an incoming WebSocket message.
        
        Expected message format (JSON) from Binance:
        {
            "stream": "btcusdt@ticker",
            "data": {
                "s": "BTCUSDT",         # Symbol (always uppercase)
                "c": "24100.50",        # Current close price (as string)
                "E": 1699999999999,     # Event time in milliseconds
                ... (other fields)
            }
        }
        Updates the shared latest_prices dictionary.
        """
        try:
            msg = json.loads(message)
            if "data" in msg:
                data = msg["data"]
                symbol = data.get("s", "").upper()  # Ensure symbol is in uppercase, e.g., "BTCUSDT"
                price_str = data.get("c", None)
                if symbol and price_str:
                    price = float(price_str)
                    timestamp = data.get("E", int(time.time() * 1000))
                    # Update the shared latest_prices dictionary with the latest price and timestamp.
                    self.latest_prices[symbol] = {
                        "price": price,
                        "last_update": timestamp
                    }
                    # Uncomment the next line to debug each price update.
                    # print(f"[WebSocket] Updated {symbol}: {price} at {timestamp}")
        except Exception as e:
            print(f"[WebSocket] Error processing message: {e}")
