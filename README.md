# cryptoarb
Triangular Arbitrage for Cryptocurrencies  
  

RUNNING INSTRUCTIONS (Windows Only):  
`Set-ExecutionPolicy Unrestricted -Scope Process -Force; .\setup.ps1`

---

## How It Works

1. **Live Data Ingestion:**  
   - The **WebSocketClient** connects to Binance’s WebSocket API, subscribing to combined ticker streams (e.g., `btcusdt@ticker`, `ethusdt@ticker`, etc.).  
   - It continuously listens for price updates, parses incoming JSON messages, and updates a shared in-memory dictionary (`latest_prices`) with the most recent prices.

2. **Arbitrage Detection:**  
   The **ArbitrageEngine** runs at regular intervals (e.g., every 1 second) and performs two kinds of checks:
   - **Triangular Arbitrage:**  
     Iterates over predefined currency triplets (such as `("USDT", "BTC", "ETH")`), retrieves conversion rates (handling inversion if necessary), applies fee adjustments, and checks if the effective product exceeds 1. If profitable, it triggers a simulated trade.
   - **Bellman-Ford Arbitrage:**  
     Constructs a graph from the live price data (using the transformation `-log(rate)`) and applies the Bellman-Ford algorithm to detect negative cycles. When a negative cycle is found, it computes the potential profit and, if profitable, triggers a simulated trade.

3. **Simulated Trade Execution:**  
   - The **PaperTrader** class simulates order execution by updating virtual balances (for example, starting with 1000 USDT) instead of executing real trades.  
   - For each detected opportunity, it simulates the conversion (applying fees for each leg) and updates the wallet.  
   - Detailed logs (including timestamp, strategy, trade path, amounts, profit, and new balances) are maintained for later analysis.

4. **Logging and Monitoring:**  
   - All simulated trades and significant events (such as WebSocket reconnections or detection errors) are logged to the console and optionally to a file.  
   - This logging facilitates later review and strategy evaluation.

---

## Deployment Overview (for later)

This codebase is designed for easy deployment on cloud platforms like AWS. Two common deployment options are:

- **AWS EC2 Deployment:**  
  Run the bot on a cost-effective EC2 instance (e.g., a t3.micro) using a Python virtual environment. The README includes instructions for installing dependencies, launching the bot with tools like `screen` or `tmux`, and ensuring continuous operation.

- **Docker Deployment with AWS ECS/Fargate:**  
  Use the provided Dockerfile to containerize the application. Deploy the container to AWS ECS/Fargate for managed scalability and cost efficiency. Detailed steps for building, pushing, and running the Docker image are included in the repository.

---

## Key Features

- **Live Data Handling:**  
  Processes real-time data from Binance without requiring historical data files.

- **Dual Arbitrage Strategies:**  
  Implements both triangular arbitrage and Bellman-Ford based multi-currency arbitrage to maximize opportunity detection.

- **Paper Trading Simulation:**  
  Simulates trades by updating a virtual wallet and logging each trade, allowing you to assess the profitability of the strategies without risk.

- **Modular and Extensible Design:**  
  The code is divided into clear modules (`websocket_client.py`, `arbitrage_engine.py`, `paper_trader.py`) with thorough inline comments, making it easy to understand, maintain, and extend.

- **Cost-Effective and Scalable:**  
  Designed to run asynchronously for efficiency and can be deployed on low-cost cloud instances or container platforms.

