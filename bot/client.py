"""
client.py — Binance Futures Testnet API wrapper

This file is the "middle layer" between your code and Binance's servers.
Think of it like a translator: you say "place an order", and this file
converts that into the exact HTTP request Binance expects.

Key concepts used here:
- HMAC SHA256 signing: Binance requires every request to be "signed"
  with your secret key to prove it's really you.
- REST API: We send HTTP requests (like a browser does) to Binance's
  server, and it sends back JSON data.
- Server time sync: We fetch Binance's clock and adjust our timestamp
  to avoid -1021 "timestamp outside recvWindow" errors.
- recvWindow: We tell Binance to accept our request up to 10 seconds
  after the timestamp, handling slow network connections.

Order type notes:
- MARKET     → /fapi/v1/order, executes immediately
- LIMIT      → /fapi/v1/order, waits for your price
- STOP       → /fapi/v1/order with type=STOP_MARKET
               Binance Futures uses STOP_MARKET for stop orders on the
               standard endpoint. When price hits stopPrice, a market
               order fires automatically.
"""

import time
import hmac
import hashlib
import requests
from bot.logging_config import get_logger

logger = get_logger(__name__)

# The base URL for Binance Futures TESTNET (not real money!)
BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    """
    A wrapper around Binance Futures Testnet REST API.

    'Wrapper' means we're wrapping the raw HTTP calls in nice Python methods
    so the rest of the code doesn't need to worry about signing, headers, etc.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Constructor — called when you do: client = BinanceClient(key, secret)

        Args:
            api_key:    Your public API key from Binance Testnet
            api_secret: Your private secret key (never share this!)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        # requests.Session() reuses the same TCP connection for speed
        self.session = requests.Session()
        # Every request must include this header so Binance knows who you are
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.info("BinanceClient initialized (Testnet)")

    def _get_server_time_offset(self) -> int:
        """
        Fetches Binance server time and calculates the offset from your
        local clock, accounting for network round-trip delay.

        WHY IS THIS NEEDED?
        Binance rejects requests (error -1021) if your timestamp differs
        from their server clock by more than recvWindow milliseconds.
        This happens when your PC clock is out of sync OR when network
        latency to the testnet is high (India to Binance servers can be slow).

        HOW IT WORKS (NTP-style midpoint technique):
        1. Record local time BEFORE the request  (t_before)
        2. Ask Binance: "what time is it?"       (server_time)
        3. Record local time AFTER the response  (t_after)
        4. Round-trip = t_after - t_before
        5. The server processed our request at roughly the midpoint,
           so: estimated_server_now = server_time + round_trip / 2
        6. offset = estimated_server_now - t_after

        Adding this offset to every timestamp keeps us in sync even
        when network latency is several seconds.

        Returns:
            Integer offset in milliseconds (can be negative)
        """
        url = BASE_URL + "/fapi/v1/time"
        try:
            t_before = int(time.time() * 1000)
            response = self.session.get(url, timeout=10)
            t_after = int(time.time() * 1000)

            server_time = response.json()["serverTime"]
            round_trip = t_after - t_before

            # Estimate server's clock at the moment we finish receiving
            offset = server_time - t_after

            logger.debug(f"Server time offset: {offset}ms | round-trip: {round_trip}ms")
            return offset
        except Exception as e:
            logger.warning(f"Could not get server time offset: {e}. Using local time.")
            return 0

    def _sign(self, params: dict) -> dict:
        """
        Signs the request parameters using HMAC-SHA256.

        WHY SIGNING? Binance needs to verify that the request truly came
        from you and wasn't tampered with. It's like a digital signature.

        HOW IT WORKS:
        1. Fetch server time offset so our timestamp matches Binance's clock
        2. Add recvWindow so Binance tolerates up to 10s of latency
        3. Convert params to a query string: "symbol=BTCUSDT&side=BUY&..."
        4. Use your secret key + HMAC-SHA256 to create a unique hash
        5. Attach that hash as 'signature' — Binance verifies it on their end

        Args:
            params: The request parameters as a dictionary

        Returns:
            The same params dict with 'timestamp', 'recvWindow', 'signature' added
        """
        # Sync timestamp with Binance server clock (fixes -1021 errors)
        offset = self._get_server_time_offset()
        params["timestamp"] = int(time.time() * 1000) + offset

        # recvWindow: how many milliseconds Binance will accept after the timestamp.
        # Default is 5000ms; we use 10000ms to handle slow/high-latency connections.
        params["recvWindow"] = 10000

        # Convert dict to URL query string: {"a": 1, "b": 2} -> "a=1&b=2"
        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        # Create HMAC-SHA256 signature
        # hmac.new(key, message, algorithm) — both must be bytes, so .encode()
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()  # convert binary hash to hex string

        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """
        Makes a signed HTTP request to Binance.

        This is the core method — all other methods call this one.

        Args:
            method:   "GET" or "POST"
            endpoint: URL path, e.g. "/fapi/v1/order"
            params:   Dictionary of parameters to send

        Returns:
            Parsed JSON response as a Python dictionary

        Raises:
            requests.exceptions.RequestException: on network errors
            Exception: on Binance API errors (non-200 status)
        """
        if params is None:
            params = {}

        # Sign the params (adds timestamp + recvWindow + signature)
        signed_params = self._sign(params)
        url = BASE_URL + endpoint

        logger.info(f"API Request -> {method} {endpoint} | params: {params}")

        try:
            if method == "GET":
                response = self.session.get(url, params=signed_params, timeout=15)
            elif method == "POST":
                response = self.session.post(url, params=signed_params, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info(
                f"API Response <- status={response.status_code} | "
                f"body={response.text[:300]}"
            )

            # If Binance returned an error (4xx, 5xx), raise an exception
            response.raise_for_status()

            return response.json()

        except requests.exceptions.ConnectionError:
            logger.error("Network error: Could not connect to Binance Testnet")
            raise
        except requests.exceptions.Timeout:
            logger.error("Request timed out after 15 seconds")
            raise
        except requests.exceptions.HTTPError as e:
            # Binance returns error details in JSON even on error responses
            try:
                error_data = response.json()
                logger.error(f"Binance API error: {error_data}")
                raise Exception(
                    f"Binance API Error {error_data.get('code')}: {error_data.get('msg')}"
                ) from e
            except Exception:
                raise

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
    ) -> dict:
        """
        Places a futures order on Binance Testnet.

        Supported order types:
        - MARKET  -> executes immediately at best price
        - LIMIT   -> waits until market reaches your price (GTC)
        - STOP    -> STOP_MARKET: fires a market order when stopPrice is hit.
                     This is the standard stop-loss on Binance Futures.
                     The --price flag is not needed for this order type.

        Args:
            symbol:     Trading pair, e.g. "BTCUSDT"
            side:       "BUY" or "SELL"
            order_type: "MARKET", "LIMIT", or "STOP"
            quantity:   How much to buy/sell
            price:      Required for LIMIT orders only
            stop_price: Required for STOP orders (the trigger price)

        Returns:
            Order response from Binance as a dictionary
        """
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
        }

        if order_type == "MARKET":
            # Executes immediately at the best available market price
            params["type"] = "MARKET"

        elif order_type == "LIMIT":
            # Open order that waits until price reaches your target
            if price is None:
                raise ValueError("LIMIT orders require a --price")
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = "GTC"  # Good Till Cancelled

        elif order_type == "STOP":
            # STOP_MARKET: when market price touches stopPrice,
            # a MARKET order fires automatically.
            # Binance Futures uses STOP_MARKET (not STOP) on /fapi/v1/order.
            # The plain "STOP" type belongs to the Algo API endpoint.
            if stop_price is None:
                raise ValueError("STOP orders require --stop-price")
            params["type"] = "STOP_MARKET"
            params["stopPrice"] = stop_price
            params["closePosition"] = "false"

        logger.info(f"Placing order: {params}")
        return self._request("POST", "/fapi/v1/order", params)

    def get_account_info(self) -> dict:
        """Fetches your futures account balance and info."""
        return self._request("GET", "/fapi/v2/account")

    def get_exchange_info(self) -> dict:
        """Fetches trading rules for all symbols (no auth needed)."""
        return self._request("GET", "/fapi/v1/exchangeInfo")
