import numpy as np
import pandas as pd
from typing import List, Dict, Literal

RiskProfile = Literal['conservative', 'balanced', 'aggressive']


class PortfolioOptimizer:
    def __init__(self, tickers: List[str], returns: pd.DataFrame):
        self.tickers = tickers
        self.returns = returns
        self.annual_returns = ((1 + returns.mean()) ** 250) - 1
        self.annual_cov = returns.cov() * 250
        self.num_assets = len(tickers)

    def simulate_portfolios(self, num_portfolios: int = 100_000) -> pd.DataFrame:
        results = []
        for _ in range(num_portfolios):
            weights = np.random.random(self.num_assets)
            weights /= np.sum(weights)

            # Constraint: no single asset over 40%
            if any(w > 0.4 for w in weights):
                continue

            # Constraint: at least 3 assets with >5% weight
            if sum(w > 0.05 for w in weights) < 3:
                continue

            port_return = np.dot(weights, self.annual_returns)
            port_volatility = np.sqrt(np.dot(weights.T, np.dot(self.annual_cov, weights)))
            if port_volatility == 0:
                continue

            sharpe_ratio = port_return / port_volatility
            if sharpe_ratio <= 0:
                continue

            results.append({
                "Return": port_return,
                "Volatility": port_volatility,
                "Sharpe Ratio": sharpe_ratio,
                **{self.tickers[i]: weights[i] for i in range(self.num_assets)}
            })

        return pd.DataFrame(results)

    def choose_optimal_portfolio(self, profile: RiskProfile, portfolios: pd.DataFrame) -> Dict:
        if portfolios.empty:
            raise ValueError("No portfolios passed the constraints.")

        if profile == 'conservative':
            return portfolios.loc[portfolios['Volatility'].idxmin()].to_dict()
        elif profile == 'aggressive':
            return portfolios.loc[portfolios['Return'].idxmax()].to_dict()
        else:
            return portfolios.loc[portfolios['Sharpe Ratio'].idxmax()].to_dict()
