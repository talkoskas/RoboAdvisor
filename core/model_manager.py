import numpy as np
import pandas as pd
from typing import List, Literal, Dict

from models.markowitz_model import MarkowitzModel

RiskProfile = Literal['conservative', 'balanced', 'aggressive']


class ModelManager:
    def __init__(self):
        self.models = {}

    def add_model(self, name: str, model: MarkowitzModel):
        self.models[name] = model

    def get_model(self, name: str) -> MarkowitzModel:
        return self.models.get(name)

    def train(self, name: str, tickers: List[str], returns: pd.DataFrame):
        model = MarkowitzModel(tickers, returns)
        model.train()
        self.add_model(name, model)

    def get_optimal_portfolio(self, name: str, profile: RiskProfile, num_portfolios: int = 100_000) -> Dict:
        model = self.get_model(name)
        portfolios = model.run_simulation(num_portfolios)
        return model.get_optimal_portfolio(profile, portfolios)
