"""
cli.py — Command-Line Interface entry point

This is the file users run directly. It:
1. Parses command-line arguments (what the user typed)
2. Loads API keys from environment variables
3. Validates inputs
4. Places the order
5. Prints results

WHAT IS argparse?
argparse is Python's built-in library for handling command-line arguments.
When you type:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

argparse reads those "--symbol", "--side" etc. and makes them available
as variables in your code.

HOW TO RUN (examples):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000
    python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 45000 --stop-price 44500
"""

import argparse
import os
import sys

# Load .env file automatically if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # It's optional; user can also export vars manually

from bot.logging_config import setup_logging, get_logger
from bot.client import BinanceClient
from bot.validators import validate_all
from bot.orders import place_order, print_order_summary, print_order_result


def build_parser() -> argparse.ArgumentParser:
    """
    Creates and configures the argument parser.

    This defines all the flags the user can pass on the command line.
    Each add_argument() call defines one flag.
    """
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="🤖 Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Market BUY:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  Limit SELL:
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000

  Stop-Limit BUY (bonus order type):
    python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 45000 --stop-price 44500
        """,
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol. Example: BTCUSDT, ETHUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",  # store as args.order_type (not args.type)
        required=True,
        choices=["MARKET", "LIMIT", "STOP", "market", "limit", "stop"],
        help="Order type: MARKET, LIMIT, or STOP (stop-limit)",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Amount to trade. Example: 0.001 for BTC",
    )
    parser.add_argument(
        "--price",
        default=None,
        help="Limit price. Required for LIMIT and STOP orders.",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",  # store as args.stop_price
        default=None,
        help="Trigger price for STOP orders.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",  # sets to True if flag is present, False otherwise
        help="Enable DEBUG logging (more verbose output)",
    )

    return parser


def load_api_credentials() -> tuple[str, str]:
    """
    Loads API key and secret from environment variables.

    WHY ENVIRONMENT VARIABLES?
    Hardcoding API keys in your source code is a huge security risk —
    if you ever upload the code to GitHub, everyone can see your keys!
    Environment variables keep secrets outside your code.

    You can set them in a .env file:
        BINANCE_API_KEY=your_key_here
        BINANCE_API_SECRET=your_secret_here

    Or export them in your terminal:
        export BINANCE_API_KEY=your_key_here
        export BINANCE_API_SECRET=your_secret_here

    Returns:
        Tuple of (api_key, api_secret)

    Raises:
        SystemExit: if either variable is missing
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("\n❌ ERROR: Missing API credentials!")
        print("Please set these environment variables:")
        print("  BINANCE_API_KEY=your_key_here")
        print("  BINANCE_API_SECRET=your_secret_here")
        print("\nTip: Create a .env file in the project root with these values.")
        sys.exit(1)  # Exit with error code 1

    return api_key, api_secret


def main():
    """
    Main entry point — orchestrates everything.

    Flow:
    1. Parse CLI arguments
    2. Set up logging
    3. Load API keys
    4. Validate inputs
    5. Place order
    6. Print result
    """
    import logging

    parser = build_parser()
    args = parser.parse_args()

    # Step 1: Set up logging (debug mode shows more detail)
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Trading Bot started")
    logger.info(
        f"Args: symbol={args.symbol} side={args.side} "
        f"type={args.order_type} qty={args.quantity} "
        f"price={args.price} stop_price={args.stop_price}"
    )

    # Step 2: Load API credentials
    api_key, api_secret = load_api_credentials()

    # Step 3: Validate all inputs
    # This raises ValueError with a helpful message if anything is wrong
    try:
        validated = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n❌ Invalid input: {e}\n")
        sys.exit(1)

    # Step 4: Print what we're about to do
    print_order_summary(validated)

    # Step 5: Create the client and place the order
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    result = place_order(
        client=client,
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated.get("price"),
        stop_price=validated.get("stop_price"),
    )

    # Step 6: Print results
    print_order_result(result)

    # Exit with appropriate code (0 = success, 1 = failure)
    # This is useful for scripts that check if the command succeeded
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    # This block only runs when you execute the file directly:
    #   python cli.py ...
    # It does NOT run when another file imports cli.py
    main()
