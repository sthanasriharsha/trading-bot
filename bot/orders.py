"""
orders.py — Order placement logic and result formatting

This file sits between the CLI (user interface) and the BinanceClient (API).
Its job is to:
1. Call the client to place the order
2. Format the response into something readable
3. Handle any errors gracefully

This separation of concerns keeps the code clean:
- cli.py  → deals with user input/output
- orders.py → deals with order logic
- client.py → deals with HTTP/API details
"""

from bot.client import BinanceClient
from bot.logging_config import get_logger

logger = get_logger(__name__)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
    stop_price: float = None,
) -> dict:
    """
    Places an order and returns a formatted result dictionary.

    Args:
        client:     An initialized BinanceClient instance
        symbol:     e.g. "BTCUSDT"
        side:       "BUY" or "SELL"
        order_type: "MARKET", "LIMIT", or "STOP"
        quantity:   Amount to trade
        price:      Limit price (LIMIT/STOP only)
        stop_price: Trigger price (STOP only)

    Returns:
        dict with keys:
          - success (bool)
          - order_id
          - status
          - symbol
          - side
          - type
          - orig_qty
          - executed_qty
          - avg_price
          - raw_response (the full Binance response)
          - error (only if success is False)
    """
    logger.info(
        f"Placing {order_type} {side} order | symbol={symbol} | "
        f"qty={quantity} | price={price} | stop_price={stop_price}"
    )

    try:
        # Call the client's place_order method
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        # Parse the response
        # Binance returns avgPrice as "0" for orders not yet filled
        avg_price = float(response.get("avgPrice", 0))

        result = {
            "success":      True,
            "order_id":     response.get("orderId"),
            "status":       response.get("status"),
            "symbol":       response.get("symbol"),
            "side":         response.get("side"),
            "type":         response.get("type"),
            "orig_qty":     float(response.get("origQty", 0)),
            "executed_qty": float(response.get("executedQty", 0)),
            "avg_price":    avg_price,
            "raw_response": response,
        }

        logger.info(
            f"Order placed successfully | orderId={result['order_id']} | "
            f"status={result['status']} | executedQty={result['executed_qty']}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to place order: {e}")
        return {
            "success": False,
            "error":   str(e),
        }


def print_order_summary(params: dict) -> None:
    """
    Prints a summary of what order is ABOUT TO be placed.
    Called before the actual API call so the user can see what's happening.

    Args:
        params: Validated order parameters dictionary
    """
    print("\n" + "=" * 55)
    print("         📋  ORDER REQUEST SUMMARY")
    print("=" * 55)
    print(f"  Symbol     : {params['symbol']}")
    print(f"  Side       : {params['side']}")
    print(f"  Order Type : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")

    if params.get("price"):
        print(f"  Price      : {params['price']}")
    if params.get("stop_price"):
        print(f"  Stop Price : {params['stop_price']}")

    print("=" * 55)


def print_order_result(result: dict) -> None:
    """
    Prints the result of an order — either success details or error message.

    Args:
        result: The dictionary returned by place_order()
    """
    if result["success"]:
        print("\n" + "=" * 55)
        print("         ✅  ORDER PLACED SUCCESSFULLY")
        print("=" * 55)
        print(f"  Order ID      : {result['order_id']}")
        print(f"  Status        : {result['status']}")
        print(f"  Symbol        : {result['symbol']}")
        print(f"  Side          : {result['side']}")
        print(f"  Type          : {result['type']}")
        print(f"  Orig Qty      : {result['orig_qty']}")
        print(f"  Executed Qty  : {result['executed_qty']}")

        if result["avg_price"] > 0:
            print(f"  Avg Fill Price: {result['avg_price']}")
        else:
            print(f"  Avg Fill Price: (not filled yet)")

        print("=" * 55 + "\n")

    else:
        print("\n" + "=" * 55)
        print("         ❌  ORDER FAILED")
        print("=" * 55)
        print(f"  Error: {result['error']}")
        print("=" * 55 + "\n")
