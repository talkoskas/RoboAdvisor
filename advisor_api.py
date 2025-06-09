from flask import Flask, request, jsonify
from models.markowitz_model import MarkowitzModel
from core.model_manager import ModelManager
from data_layer.fetcher_adapter import MarketDataFetcher, YahooFinanceFetcher
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/portfolio', methods=['POST'])
def get_portfolio():
    try:
        data = request.get_json()
        risk_profile = data.get("risk_profile", "balanced")

        tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "JNJ", "XOM", "SPY"
        ]
        start_date = "2020-01-01"
        end_date = "2025-06-01"

        # Step 1: Fetch data
        fetcher = MarketDataFetcher(YahooFinanceFetcher())
        df = fetcher.get_price_data(tickers, start_date, end_date)
        returns = df.pct_change().dropna()

        # Step 2: Train model
        manager = ModelManager()
        manager.train(name="markowitz", tickers=tickers, returns=returns)

        # Step 3: Get optimal portfolio
        portfolios = manager.get_model("markowitz").run_simulation(100_000)
        optimal = manager.get_model("markowitz").get_optimal_portfolio(risk_profile, portfolios)

        return jsonify(optimal)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
