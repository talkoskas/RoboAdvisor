from abc import ABC, abstractmethod
import yfinance as yf
import pandas as pd
from typing import List


class AbstractMarketDataFetcher(ABC):
    @abstractmethod
    def fetch(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        pass


class YahooFinanceFetcher(AbstractMarketDataFetcher):
    def fetch(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        print(f"Fetching data from Yahoo Finance for: {tickers}")
        df = yf.download(tickers, start=start_date, end=end_date)["Close"]
        df = df.ffill().bfill()  # Fill missing values
        return df


class MarketDataFetcher:
    def __init__(self, adapter: AbstractMarketDataFetcher):
        self.adapter = adapter

    def get_price_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        return self.adapter.fetch(tickers, start_date, end_date)


# Example usage
if __name__ == "__main__":
    fetcher = MarketDataFetcher(YahooFinanceFetcher())
    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = fetcher.get_price_data(tickers, start_date="2020-01-01", end_date="2023-01-01")
    print(data.head())
