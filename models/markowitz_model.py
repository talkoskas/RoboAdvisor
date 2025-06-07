import pandas as pd
from typing import List, Literal, Dict
import matplotlib.pyplot as plt
from models.portfolio_optimizer import PortfolioOptimizer

RiskProfile = Literal['conservative', 'balanced', 'aggressive']


class MarkowitzModel:
    def __init__(self, tickers: List[str], returns: pd.DataFrame):
        self.tickers = tickers
        self.returns = returns
        self.optimizer = PortfolioOptimizer(tickers, returns)
        self.is_trained = False

    def train(self):
        # בגרסה הזו אין צורך לאמן כי החישובים נעשים באובייקט האופטימיזציה
        self.is_trained = True

    def run_simulation(self, num_portfolios: int = 100_000) -> pd.DataFrame:
        return self.optimizer.simulate_portfolios(num_portfolios)

    def get_optimal_portfolio(self, profile: RiskProfile, portfolios: pd.DataFrame) -> Dict:
        return self.optimizer.choose_optimal_portfolio(profile, portfolios)

    def plot_efficient_frontier(self, portfolios: pd.DataFrame):
        plt.figure(figsize=(10, 6))
        plt.scatter(portfolios['Volatility'], portfolios['Return'], c=portfolios['Sharpe Ratio'], cmap='viridis')
        plt.xlabel("Volatility")
        plt.ylabel("Return")
        plt.colorbar(label="Sharpe Ratio")
        plt.title("Efficient Frontier")
        plt.grid(True)
        plt.show()
