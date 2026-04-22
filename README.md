# 🤖 Binance Futures Testnet Trading Bot

A Python CLI trading bot for placing orders on Binance Futures Testnet (USDT-M).  
Built for the Primetrade.ai Python Developer Intern Assessment.

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py         # Makes `bot` a Python package
│   ├── client.py           # Binance API wrapper (HTTP requests + signing)
│   ├── orders.py           # Order placement logic + result formatting
│   ├── validators.py       # Input validation
│   └── logging_config.py   # Logging setup
├── cli.py                  # Entry point — run this file
├── logs/
│   └── trading_bot.log     # Log output (auto-created)
├── .env.example            # Template for API credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠 Setup Steps

### Step 1 — Get Binance Testnet API Keys

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Click **"Get Started"** → Log in with GitHub
3. On the dashboard, go to **API Key** section
4. Click **"Generate Key"** — copy your API Key and Secret Key somewhere safe

> ⚠️ The Secret Key is shown **only once**. Save it immediately!

---

### Step 2 — Install Python 3

Check if Python is installed:
```bash
python --version   # or: python3 --version
```

If not installed, download from [https://python.org/downloads](https://python.org/downloads)  
Make sure to check **"Add Python to PATH"** during installation on Windows.

---

### Step 3 — Download / Clone this project

**Option A — via git:**
```bash
git clone https://github.com/YOUR_USERNAME/trading_bot.git
cd trading_bot
```

**Option B — download ZIP:**  
Extract the ZIP and open a terminal inside the `trading_bot` folder.

---

### Step 4 — Create a virtual environment (recommended)

A virtual environment keeps this project's packages separate from your system Python.

```bash
# Create it
python -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate
```

You'll see `(venv)` in your terminal prompt when it's active.

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` — for making HTTP calls to Binance
- `python-dotenv` — for loading API keys from a `.env` file

---

### Step 6 — Set up API credentials

Copy the example file:
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your keys:
```
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_key_here
```

> 🔒 `.env` is listed in `.gitignore` so it will NEVER be pushed to GitHub.

---

## 🚀 How to Run

All commands are run from the `trading_bot/` directory with your venv active.

### Place a MARKET order

Buy 0.001 BTC at the current market price:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Sell 0.001 BTC at market price:
```bash
python cli.py --symbol BTCUSDT --side SELL --type MARKET --quantity 0.001
```

---

### Place a LIMIT order

Sell 0.01 ETH when price reaches $3000:
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000
```

Buy 0.001 BTC only if price drops to $40000:
```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 40000
```

---

### Place a STOP (Stop-Limit) order *(Bonus)*

Buy 0.001 BTC with a stop trigger at $44500 and limit price at $45000:
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 45000 --stop-price 44500
```

---

### Enable debug logging

Add `--debug` to see very detailed output including all request/response details:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --debug
```

---

### Get help

```bash
python cli.py --help
```

---

## 📋 Sample Output

```
=======================================================
         📋  ORDER REQUEST SUMMARY
=======================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Order Type : MARKET
  Quantity   : 0.001
=======================================================

=======================================================
         ✅  ORDER PLACED SUCCESSFULLY
=======================================================
  Order ID      : 4751906587
  Status        : FILLED
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Fill Price: 43521.5
=======================================================
```

---

## 📂 Log Files

Logs are saved to `logs/trading_bot.log` automatically.  
The log captures:
- Every API request sent (parameters, endpoint)
- Every API response received (status code, body)
- Validation steps
- Any errors or warnings

---

## ⚙️ Assumptions

1. **Testnet only** — this bot uses `https://testnet.binancefuture.com`. No real money.
2. **USDT-M Futures** — all orders are placed on USDT-margined perpetual futures.
3. **Quantity precision** — Binance has minimum order sizes per symbol (e.g. 0.001 BTC minimum for BTCUSDT). If your quantity is too small, Binance will return an error with a clear message.
4. **LIMIT order status** — a LIMIT order may show status `NEW` (not yet filled) because it's waiting for the market to reach your price. This is normal.
5. **Environment variables** — API keys must be provided via a `.env` file or exported environment variables. The program will exit with a clear message if keys are missing.

---

## 🛡️ Security Notes

- Never commit `.env` to GitHub
- Never share your API Secret Key
- Testnet keys can't be used on real Binance (different URL)

---

## 📦 Requirements

- Python 3.10+
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`
