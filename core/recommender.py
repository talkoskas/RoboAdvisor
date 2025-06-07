from typing import List, Literal, Dict
from core.model_manager import ModelManager
from data_layer.fetcher_adapter import MarketDataFetcher, YahooFinanceFetcher

RiskProfile = Literal['conservative', 'balanced', 'aggressive']


class PortfolioRecommender:
    def __init__(self):
        self.model_manager = ModelManager()
        self.fetcher = MarketDataFetcher(YahooFinanceFetcher())

    def recommend_portfolio(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        profile: RiskProfile,
        num_portfolios: int = 100_000,
        show_plot: bool = True
    ) -> Dict:
        # Step 1: Fetch historical price data
        df = self.fetcher.get_price_data(tickers, start_date, end_date)

        # Step 2: Calculate daily returns
        returns = df.pct_change().dropna()

        # Step 3: Train and register the model
        self.model_manager.train("markowitz", tickers, returns)

        # Step 4: Simulate portfolios
        model = self.model_manager.get_model("markowitz")
        portfolios = model.run_simulation(num_portfolios)

        # Step 5: Plot efficient frontier (optional)
        if show_plot:
            model.plot_efficient_frontier(portfolios)

        # Step 6: Get optimal portfolio
        optimal_portfolio = model.get_optimal_portfolio(profile, portfolios)

        return optimal_portfolio


# Example usage
if __name__ == "__main__":
    recommender = PortfolioRecommender()
    tickers = ["SPY", "QQQ", "DJI", "MSFT", "IEI", "TLT", "SHY", "GLD", "VNQ", "VEA", "VWO"]
    start_date = "2020-01-01"
    end_date = "2025-06-01"
    profile: RiskProfile = "balanced"

    result = recommender.recommend_portfolio(tickers, start_date, end_date, profile)

    print("\n=== Recommended Portfolio ===")
    for key, value in result.items():
        print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")
