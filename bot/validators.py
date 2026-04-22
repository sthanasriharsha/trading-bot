"""
validators.py — Input validation logic

This file checks whether the user's input makes sense BEFORE we send
anything to Binance. It's like a security guard at the door.

Why validate early?
- Catch typos before wasting an API call
- Give clear error messages to the user
- Prevent weird edge cases from crashing the program
"""

from bot.logging_config import get_logger

logger = get_logger(__name__)

# These are the only values Binance accepts for these fields
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


def validate_symbol(symbol: str) -> str:
    """
    Validates the trading symbol.

    Rules:
    - Must not be empty
    - Convert to uppercase (btcusdt → BTCUSDT)
    - Basic length check

    Args:
        symbol: e.g. "btcusdt" or "ETHUSDT"

    Returns:
        Uppercased symbol string

    Raises:
        ValueError: if symbol is invalid
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty. Example: BTCUSDT")

    symbol = symbol.strip().upper()

    if len(symbol) < 3 or len(symbol) > 20:
        raise ValueError(f"Symbol '{symbol}' looks invalid. Example: BTCUSDT")

    # Symbols should only have letters and digits
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' should only contain letters and numbers.")

    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """
    Validates the order side.

    Args:
        side: "BUY" or "SELL" (case-insensitive)

    Returns:
        Uppercased side string

    Raises:
        ValueError: if side is not BUY or SELL
    """
    side = side.strip().upper()

    if side not in VALID_SIDES:
        raise ValueError(f"Side must be BUY or SELL. Got: '{side}'")

    logger.debug(f"Side validated: {side}")
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validates the order type.

    Args:
        order_type: "MARKET", "LIMIT", or "STOP"

    Returns:
        Uppercased order type string

    Raises:
        ValueError: if order type is not recognized
    """
    order_type = order_type.strip().upper()

    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {VALID_ORDER_TYPES}. Got: '{order_type}'"
        )

    logger.debug(f"Order type validated: {order_type}")
    return order_type


def validate_quantity(quantity_str: str) -> float:
    """
    Validates and converts the quantity input.

    Args:
        quantity_str: String input from the user, e.g. "0.001"

    Returns:
        Float value of quantity

    Raises:
        ValueError: if quantity is not a valid positive number
    """
    try:
        quantity = float(quantity_str)
    except (ValueError, TypeError):
        raise ValueError(f"Quantity must be a number. Got: '{quantity_str}'")

    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {quantity}")

    # Binance has minimum order sizes; this is a basic sanity check
    if quantity > 1_000_000:
        raise ValueError(f"Quantity {quantity} seems unrealistically large. Please check.")

    logger.debug(f"Quantity validated: {quantity}")
    return quantity


def validate_price(price_str: str, field_name: str = "price") -> float:
    """
    Validates and converts a price input.

    Args:
        price_str:  String input from user, e.g. "45000.50"
        field_name: Name of the field (for better error messages)

    Returns:
        Float value of price

    Raises:
        ValueError: if price is not a valid positive number
    """
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a number. Got: '{price_str}'")

    if price <= 0:
        raise ValueError(f"{field_name} must be greater than 0. Got: {price}")

    logger.debug(f"{field_name} validated: {price}")
    return price


def validate_all(symbol: str, side: str, order_type: str,
                 quantity: str, price: str = None,
                 stop_price: str = None) -> dict:
    """
    Validates all inputs at once and returns a clean dictionary.

    This is the "main" validation function that the CLI calls.
    It runs all individual validators and also checks cross-field rules
    (like: LIMIT orders MUST have a price).

    Args:
        symbol:     Trading symbol
        side:       BUY or SELL
        order_type: MARKET, LIMIT, or STOP
        quantity:   Order quantity
        price:      Limit price (required for LIMIT and STOP)
        stop_price: Trigger price (required for STOP only)

    Returns:
        Dictionary with all validated and converted values

    Raises:
        ValueError: on any validation failure
    """
    result = {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity":   validate_quantity(quantity),
        "price":      None,
        "stop_price": None,
    }

    # Cross-field validation: LIMIT needs price
    if result["order_type"] == "LIMIT":
        if price is None:
            raise ValueError("LIMIT orders require --price")
        result["price"] = validate_price(price, "price")

    # Cross-field validation: STOP_MARKET only needs stop_price (the trigger)
    # No --price needed because Binance fires a MARKET order when triggered
    elif result["order_type"] == "STOP":
        if stop_price is None:
            raise ValueError("STOP orders require --stop-price (the trigger price)")
        result["stop_price"] = validate_price(stop_price, "stop_price")

    logger.info(f"All inputs validated: {result}")
    return result
