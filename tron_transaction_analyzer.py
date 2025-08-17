import os
import time
import requests
import json
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any

# Load environment variables
load_dotenv()
API_KEY = os.getenv("TRONSCAN_API_KEY")

class RateLimiter:
    """Simple rate limiter to prevent API throttling"""
    def __init__(self, calls_per_second: int = 5):
        self.calls_per_second = calls_per_second
        self.minimum_interval = 1.0 / calls_per_second
        self.last_call_time = 0

    def wait(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_call_time
        if elapsed_time < self.minimum_interval:
            time.sleep(self.minimum_interval - elapsed_time)
        self.last_call_time = time.time()

class TronscanAPI:
    """API client for Tronscan blockchain explorer"""
    def __init__(self, api_key: str, debug: bool = False):
        self.base_url = "https://apilist.tronscanapi.com/api"
        self.api_key = api_key
        self.debug = debug
        self.rate_limiter = RateLimiter(calls_per_second=5)
        self.headers = {"TRON-PRO-API-KEY": self.api_key}

    def get_trc20_transfers(self, address: str, limit: int = 100, start: int = 0) -> List[Dict]:
        """Retrieve all TRC20 token transfers for a specific address"""
        all_transfers = []
        while True:
            self.rate_limiter.wait()
            params = {"limit": limit, "start": start, "relatedAddress": address}
            response = requests.get(f"{self.base_url}/token_trc20/transfers", params=params, headers=self.headers)
            if response.status_code != 200:
                break
            data = response.json().get("token_transfers", [])
            all_transfers.extend(data)
            if len(data) < limit:
                break
            start += limit
        return all_transfers

    def format_trc20_transaction(self, transfer: Dict, address: str) -> Optional[Dict]:
        """Format transaction data and filter for USDT only"""
        timestamp_ms = transfer.get("block_ts", 0)
        date_time = datetime.fromtimestamp(timestamp_ms / 1000)
        token_info = transfer.get("tokenInfo", {})
        token_symbol = token_info.get("tokenAbbr", "Unknown")

        # Only process USDT transactions
        if token_symbol != "USDT":
            return None

        token_decimals = token_info.get("tokenDecimal", 0)
        amount = float(transfer.get("quant", "0")) / (10 ** token_decimals)
        direction = "incoming" if transfer.get("to_address", "").lower() == address.lower() else "outgoing"

        # Create shortened address for visualization
        short_address = address[:8] + "..." + address[-4:]

        return {
            "timestamp": timestamp_ms,
            "date_time": date_time,
            "wallet": address,
            "wallet_short": short_address,
            "amount": amount,
            "direction": direction,
            "hash": transfer.get("transaction_id", "Unknown"),
        }

    def plot_transaction_volumes(self, transactions: List[Dict]):
        """Generate interactive visualization of transaction data"""
        df = pd.DataFrame(transactions).dropna()
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Create custom hover data
        hover_data = {
            "wallet": False,
            "wallet_short": False,
            "amount": True,
            "hash": False,
            "timestamp": False,
        }

        # Color scheme with high contrast
        color_map = {"incoming": "#32CD32", "outgoing": "#FF4500"}

        fig = px.scatter(
            df,
            x="timestamp",
            y="wallet_short",
            size="amount",
            size_max=30,
            color="direction",
            hover_name="wallet_short",
            hover_data=hover_data,
            title="USDT Transactions Over Time by Wallet",
            labels={
                "amount": "Transaction Volume (USDT)",
                "wallet_short": "Wallet Address",
                "direction": "",
            },
            opacity=0.8,
            color_discrete_map=color_map,
            height=800,
            width=1200,
        )

        # Improve layout and appearance
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Arial, sans-serif", size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="lightgray",
                gridwidth=0.5,
                zeroline=False,
                title_font=dict(size=14),
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                title_font=dict(size=14),
            ),
            margin=dict(l=20, r=20, t=50, b=20),
        )

        # Format time axis
        fig.update_xaxes(
            tickformat="%b %Y",
            dtick="M1",
            tickangle=-45,
        )
        fig.show()

def main():
    """Main function to process addresses and visualize transactions"""
    if not API_KEY:
        print("Error: TRONSCAN_API_KEY not found in .env file")
        return

    client = TronscanAPI(API_KEY)
    addresses_file = input("Enter the filename containing TRON addresses: ")

    try:
        with open(addresses_file, "r") as file:
            addresses = [line.strip() for line in file if line.strip()]

        all_transactions = []
        for address in addresses:
            trc20_transfers = client.get_trc20_transfers(address)
            formatted_transfers = [client.format_trc20_transaction(tx, address) for tx in trc20_transfers]
            all_transactions.extend(filter(None, formatted_transfers))

        client.plot_transaction_volumes(all_transactions)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
