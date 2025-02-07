#!/usr/bin/env python3
"""
arbitrage_engine.py

This module implements the ArbitrageEngine class that detects arbitrage opportunities.
It runs two methods:
  - A triangular arbitrage check on predefined currency triplets.
  - A Bellman-Ford based multi-currency arbitrage check that detects negative cycles.
Both strategies, when profitable, trigger a simulated trade in the PaperTrader.

ARNAV'S SUMMARY: This module implements the ArbitrageEngine class, which runs both the triangular arbitrage checks
and the Bellman-Ford negative cycle detection. It uses the shared latest price data and, when an opportunity is found,
calls the appropriate method on the PaperTrader to simulate a trade.
"""

import asyncio
import math
import time

class ArbitrageEngine:
    def __init__(self, latest_prices, paper_trader):
        """
        Initialize the arbitrage engine.
        
        Args:
            latest_prices (dict): Shared dictionary containing the latest ticker prices.
            paper_trader (PaperTrader): Instance of PaperTrader to simulate trades.
        """
        self.latest_prices = latest_prices
        self.paper_trader = paper_trader
        # Predefined list of triangular triplets (currencies must be in uppercase).
        # These can later be made adaptive based on profitability.
        self.triangular_triplets = [
            ("USDT", "BTC", "ETH"),
            ("USDT", "BTC", "BNB"),
            ("BTC", "ETH", "USDT"),
            # Add more triplets as needed.
        ]
        # Fee per trade leg (0.1% fee represented as 0.001)
        self.fee_rate = 0.001
        # How often (in seconds) to run the arbitrage detection.
        self.detection_interval = 1.0

    async def detection_scheduler(self):
        """
        Scheduler that periodically runs both the triangular and Bellman-Ford arbitrage checks.
        """
        while True:
            try:
                self.run_triangular_arbitrage_check()
                self.run_bellman_ford_arbitrage_check()
            except Exception as e:
                print(f"[ArbitrageEngine] Error during detection: {e}")
            await asyncio.sleep(self.detection_interval)

    def run_triangular_arbitrage_check(self):
        """
        Check each triangular triplet for arbitrage opportunity.
        For a triplet (A, B, C), obtain rates for:
            A -> B, B -> C, and C -> A.
        Compute the effective product (after fees) and if greater than 1,
        a profitable opportunity exists.
        """
        for triplet in self.triangular_triplets:
            A, B, C = triplet  # All currencies must be uppercase
            # Construct pair symbols. We attempt both direct and inverse forms.
            pair_AB = f"{A}{B}" if f"{A}{B}" in self.latest_prices else f"{B}{A}"
            pair_BC = f"{B}{C}" if f"{B}{C}" in self.latest_prices else f"{C}{B}"
            pair_CA = f"{C}{A}" if f"{C}{A}" in self.latest_prices else f"{A}{C}"
            
            # Skip this triplet if any required pair is not available.
            if pair_AB not in self.latest_prices or pair_BC not in self.latest_prices or pair_CA not in self.latest_prices:
                continue

            # Retrieve rates using helper method (handles inversion if necessary).
            rate_AB = self.get_rate(A, B, pair_AB)
            rate_BC = self.get_rate(B, C, pair_BC)
            rate_CA = self.get_rate(C, A, pair_CA)

            if rate_AB is None or rate_BC is None or rate_CA is None:
                continue

            # Calculate raw product of the three rates.
            raw_product = rate_AB * rate_BC * rate_CA
            # Apply fee adjustments for each leg: multiply by (1 - fee_rate) for each trade.
            fee_adjustment = (1 - self.fee_rate) ** 3
            effective_product = raw_product * fee_adjustment

            # If the effective product exceeds 1, an arbitrage opportunity exists.
            if effective_product > 1:
                net_profit = effective_product - 1
                timestamp = int(time.time() * 1000)
                print(f"[Triangular] Opportunity detected for {triplet}: Profit = {net_profit*100:.2f}%")
                # Define a trade amount (for demonstration, 100 units of the base currency).
                trade_amount = 100
                self.paper_trader.execute_triangular_trade(
                    triplet, trade_amount, rate_AB, rate_BC, rate_CA, net_profit, timestamp
                )

    def get_rate(self, base, quote, pair_symbol):
        """
        Retrieve the conversion rate from base to quote for a given pair.
        
        Args:
            base (str): The base currency.
            quote (str): The quote currency.
            pair_symbol (str): The symbol key found in latest_prices (e.g., "BTCUSDT" or "USDTBTC").
        
        Returns:
            float or None: The conversion rate from base to quote. If the pair is stored in inverse order,
                           the rate is inverted.
        """
        data = self.latest_prices.get(pair_symbol, None)
        if data is None:
            return None
        price = data.get("price", None)
        if price is None:
            return None

        # Check if the pair_symbol matches base+quote directly.
        if pair_symbol == f"{base}{quote}":
            return price
        elif pair_symbol == f"{quote}{base}":
            return 1 / price if price != 0 else None
        else:
            return None

    def run_bellman_ford_arbitrage_check(self):
        """
        Construct a graph from the current prices and run the Bellman-Ford algorithm to detect
        negative cycles. A negative cycle indicates a profitable arbitrage opportunity.
        """
        graph = {}
        currencies = set()
        # Build graph edges from the latest_prices data.
        for symbol, data in self.latest_prices.items():
            # Ensure the symbol is long enough to parse (this is a simplification).
            if len(symbol) < 6:
                continue
            # For simplicity, assume that if the symbol ends with "USDT", the base is the part before "USDT".
            if symbol.endswith("USDT"):
                base = symbol[:-4]
                quote = "USDT"
            else:
                # Otherwise, split the symbol into two 3-letter currencies (this may need refinement for other pairs).
                base = symbol[:3]
                quote = symbol[3:]
            currencies.add(base)
            currencies.add(quote)
            rate = data.get("price", None)
            if rate is None or rate <= 0:
                continue
            # Compute edge weight = -log(rate * (1 - fee_rate))
            weight = -math.log(rate * (1 - self.fee_rate))
            # Add edge from base to quote.
            if base not in graph:
                graph[base] = []
            graph[base].append((quote, weight))
            # Add inverse edge.
            if rate != 0:
                inv_weight = -math.log((1 / rate) * (1 - self.fee_rate))
                if quote not in graph:
                    graph[quote] = []
                graph[quote].append((base, inv_weight))

        # Run the Bellman-Ford algorithm starting from each currency.
        for start in currencies:
            distances = {currency: float('inf') for currency in currencies}
            predecessors = {currency: None for currency in currencies}
            distances[start] = 0

            # Relax all edges |V| - 1 times.
            for _ in range(len(currencies) - 1):
                for u in graph:
                    for v, weight in graph[u]:
                        if distances[u] + weight < distances[v]:
                            distances[v] = distances[u] + weight
                            predecessors[v] = u

            # Check for negative cycles.
            for u in graph:
                for v, weight in graph[u]:
                    if distances[u] + weight < distances[v]:
                        cycle = self.reconstruct_cycle(predecessors, v)
                        if cycle:
                            # Calculate profit by simulating 1 unit traded along the cycle.
                            profit = self.calculate_cycle_profit(cycle)
                            if profit > 1:
                                net_profit = profit - 1
                                timestamp = int(time.time() * 1000)
                                print(f"[Bellman-Ford] Opportunity detected: Cycle: {cycle}, Profit: {net_profit*100:.2f}%")
                                trade_amount = 100  # Example trade amount in starting currency.
                                self.paper_trader.execute_cycle_trade(cycle, trade_amount, net_profit, timestamp)
                        return  # Exit after processing one negative cycle for simplicity.

    def reconstruct_cycle(self, predecessors, start_vertex):
        """
        Reconstruct a negative cycle from the predecessor mapping.
        
        Args:
            predecessors (dict): Mapping from each currency to its predecessor.
            start_vertex (str): The starting vertex where a negative cycle was detected.
        
        Returns:
            list: A list of currencies representing the arbitrage cycle.
        """
        cycle = []
        visited = set()
        current = start_vertex
        while current not in visited:
            visited.add(current)
            current = predecessors[current]
            if current is None:
                return None
        cycle_start = current
        cycle.append(cycle_start)
        current = predecessors[cycle_start]
        while current != cycle_start:
            cycle.append(current)
            current = predecessors[current]
        cycle.reverse()
        return cycle

    def calculate_cycle_profit(self, cycle):
        """
        Calculate the profit from executing a series of trades along a cycle.
        
        Args:
            cycle (list): List of currency symbols representing the cycle.
        
        Returns:
            float: Final amount after executing the cycle starting with 1 unit.
        """
        amount = 1.0
        for i in range(len(cycle)):
            A = cycle[i]
            B = cycle[(i + 1) % len(cycle)]
            direct_symbol = f"{A}{B}"
            inverse_symbol = f"{B}{A}"
            if direct_symbol in self.latest_prices:
                rate = self.latest_prices[direct_symbol]["price"]
            elif inverse_symbol in self.latest_prices:
                inv_rate = self.latest_prices[inverse_symbol]["price"]
                rate = 1 / inv_rate if inv_rate != 0 else 0
            else:
                rate = 1.0  # Should not occur if data is complete.
            amount = amount * rate * (1 - self.fee_rate)
        return amount
