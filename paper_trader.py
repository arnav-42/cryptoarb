#!/usr/bin/env python3
"""
paper_trader.py

This module implements the PaperTrader class which simulates order execution.
It maintains a virtual wallet (paper_balances) and records each simulated trade.

ARNAV'S SUMMARY: This module implements the PaperTrader class, which simulates trades without interacting with the live exchange.
It updates virtual balances and logs each trade’s details.
"""

import copy

class PaperTrader:
    def __init__(self, initial_balances):
        """
        Initialize the paper trader with starting virtual balances.
        
        Args:
            initial_balances (dict): A dictionary mapping currency symbols to starting balances.
                                     Example: {"USDT": 1000.0, "BTC": 0.0, "ETH": 0.0, ...}
        """
        self.balances = initial_balances
        self.trade_log = []  # List to store logs of simulated trades.

    def execute_triangular_trade(self, triplet, trade_amount, rate_AB, rate_BC, rate_CA, net_profit, timestamp):
        """
        Simulate execution of a triangular arbitrage trade.
        
        Args:
            triplet (tuple): A tuple of three currency symbols (A, B, C).
            trade_amount (float): The amount of the starting currency (A) to trade.
            rate_AB (float): Conversion rate from A to B.
            rate_BC (float): Conversion rate from B to C.
            rate_CA (float): Conversion rate from C back to A.
            net_profit (float): The net profit multiplier (profit percentage expressed as a fraction).
            timestamp (int): The detection timestamp in milliseconds.
        """
        A, B, C = triplet
        # Check for sufficient balance in currency A.
        if self.balances.get(A, 0) < trade_amount:
            print(f"[PaperTrader] Insufficient balance in {A} for triangular trade.")
            return
        
        # Simulate each conversion, applying a fee of 0.1% per trade leg.
        amount_B = trade_amount * rate_AB * (1 - 0.001)
        amount_C = amount_B * rate_BC * (1 - 0.001)
        final_amount_A = amount_C * rate_CA * (1 - 0.001)
        
        # Update virtual balance for currency A.
        old_balance = self.balances.get(A, 0)
        self.balances[A] = old_balance - trade_amount + final_amount_A
        
        # Create a detailed trade log entry.
        trade_details = {
            "timestamp": timestamp,
            "strategy": "Triangular",
            "path": f"{A} -> {B} -> {C} -> {A}",
            "initial_amount": trade_amount,
            "final_amount": final_amount_A,
            "net_profit": final_amount_A - trade_amount,
            "balances_after": copy.deepcopy(self.balances)
        }
        self.trade_log.append(trade_details)
        print(f"[PaperTrader] Executed triangular trade: {trade_details}")

    def execute_cycle_trade(self, cycle, trade_amount, net_profit, timestamp):
        """
        Simulate execution of a multi-currency arbitrage trade based on a cycle detected via Bellman-Ford.
        
        Args:
            cycle (list): A list of currency symbols representing the arbitrage cycle.
            trade_amount (float): The amount in the starting currency to trade.
            net_profit (float): The net profit multiplier (profit percentage expressed as a fraction).
            timestamp (int): The detection timestamp in milliseconds.
        """
        # Use the first currency in the cycle as the starting currency.
        start_currency = cycle[0]
        if self.balances.get(start_currency, 0) < trade_amount:
            print(f"[PaperTrader] Insufficient balance in {start_currency} for cycle trade.")
            return
        
        # For simulation, assume perfect execution through the cycle.
        final_amount = trade_amount * (1 + net_profit)
        
        # Update the virtual balance.
        old_balance = self.balances.get(start_currency, 0)
        self.balances[start_currency] = old_balance - trade_amount + final_amount
        
        # Create a detailed trade log entry.
        trade_details = {
            "timestamp": timestamp,
            "strategy": "BellmanFord",
            "path": " -> ".join(cycle) + f" -> {cycle[0]}",
            "initial_amount": trade_amount,
            "final_amount": final_amount,
            "net_profit": final_amount - trade_amount,
            "balances_after": copy.deepcopy(self.balances)
        }
        self.trade_log.append(trade_details)
        print(f"[PaperTrader] Executed cycle trade: {trade_details}")
