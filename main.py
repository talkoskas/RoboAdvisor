from models.markowitz_model import MarkowitzModel
from core.model_manager import ModelManager
from data_layer.fetcher_adapter import MarketDataFetcher, YahooFinanceFetcher


def run_demo():
    # טיקרים מגוונים יותר
    tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",   # טכנולוגיה
    "META", "TSLA", "INTC", "AMD", "CRM",      # טכנולוגיה/AI
    "JPM", "BAC", "WFC", "GS", "V", "MA",       # פיננסים
    "JNJ", "PFE", "MRK", "UNH",                 # בריאות
    "XOM", "CVX", "BP",                         # אנרגיה
    "SPY", "QQQ", "DIA", "VOO", "VTI",          # אינדקסים כלליים
    "IEI", "TLT", "SHY", "BND", "AGG",          # אג״חים (ETF)
    "GLD", "SLV",                               # סחורות: זהב וכסף
    "VNQ", "XLRE",                              # נדל"ן
    "VEA", "VWO", "EWJ", "EFA", "EEM"           # בינלאומיים
]
    start_date = "2020-01-01"
    end_date = "2025-06-01"

    # שלב 1: שליפת נתונים
    fetcher = MarketDataFetcher(YahooFinanceFetcher())
    df = fetcher.get_price_data(tickers, start_date, end_date)

    # שלב 2: חישוב תשואות יומיות
    returns = df.pct_change().dropna()

    # שלב 3: יצירת מנהל המודלים
    manager = ModelManager()
    manager.train(name="markowitz", tickers=tickers, returns=returns)

    # שלב 4: עבור כל פרופיל סיכון – צור תיק והצג תוצאות
    for profile in ["conservative", "balanced", "aggressive"]:
        print(f"\n=== Optimal Portfolio ({profile.capitalize()}) ===")
        portfolios = manager.get_model("markowitz").run_simulation(num_portfolios=100_000)
        optimal = manager.get_model("markowitz").get_optimal_portfolio(profile, portfolios)

        for key, value in optimal.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")

        # הצגת חזית היעילות
        manager.get_model("markowitz").plot_efficient_frontier(portfolios)


if __name__ == "__main__":
    run_demo()
