import pandas as pd
from datetime import datetime, timedelta


class ChatbotEngine:
    def __init__(self, model, data_handler, graph_generator, intent_detector):
        self.model = model
        self.data_handler = data_handler
        self.graph_generator = graph_generator
        self.intent_detector = intent_detector

    def handle_input(self, user_input: str) -> dict:
        try:
            intent_data = self.intent_detector.detect(user_input)

            if intent_data["intent"] == "sector_values":
                return self._handle_sector_intent(intent_data)

            elif intent_data["intent"] == "graph":
                return self._handle_graph_intent(intent_data)

            elif intent_data["intent"] == "compare":
                return self._handle_compare_intent(intent_data)

            else:
                # fallback text-based Gemini response
                text = self.model.generate_content(
                    user_input + " add a sad emoji wherever you find fitting."
                ).text
                return {"text": text}

        except Exception as e:
            return {"text": f"Oops, something went wrong 😱: {str(e)}"}

    # =============================
    # Intent Handlers
    # =============================

    def _handle_sector_intent(self, intent_data):
        sector = intent_data["sector"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 3, 13)

        actual_df = self.data_handler.get_sector_actuals(sector, start_date, end_date)
        predicted_df = self.data_handler.get_sector_predictions(sector, start_date, end_date)
        best_model_df = pd.read_csv(self.data_handler.best_model_path)

        forecast_dfs = []
        ticker_to_company = {v: k for k, v in self.data_handler.ticker_mapping.items()}

        unique_tickers = actual_df["Ticker"].dropna().unique()
        for ticker in unique_tickers:
            try:
                model = best_model_df.loc[best_model_df["Company"] == ticker, "Model"].values[0]
                ap_data = self.data_handler.extract_by_model(ticker, model, start_date, end_date)
                last_date = ap_data["Date"].max()
                forecast = self.data_handler.extract_forecasted_values(ticker, last_date, ap_data)
                forecast["Company"] = ticker_to_company.get(ticker.replace(".TA", ""), ticker)
                forecast["Ticker"] = ticker
                forecast_dfs.append(forecast)
            except:
                continue

        full_forecast_df = pd.concat(forecast_dfs) if forecast_dfs else pd.DataFrame()

        # Generate plots
        fig_actual = self.graph_generator.generate_sector_graph(actual_df, "Actual", sector)
        fig_pred = self.graph_generator.generate_sector_graph(predicted_df, "Predicted", sector)
        fig_forecast = self.graph_generator.generate_sector_graph(full_forecast_df, "Forecasted", sector)

        summary = self.generate_sector_summary(actual_df, predicted_df, full_forecast_df, ticker_to_company, sector)
        return {"text": summary, "graphs": [fig_actual, fig_pred, fig_forecast]}

    def _handle_graph_intent(self, intent_data):
        company = intent_data["company"].upper()
        ticker = self.intent_detector.resolve_ticker(company) + ".TA"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 3, 13)

        best_model_df = pd.read_csv(self.data_handler.best_model_path)
        model = best_model_df.loc[best_model_df["Company"] == ticker, "Model"].values[0]

        data = self.data_handler.extract_by_model(ticker, model, start_date, end_date)
        last_date = data["Date"].max()
        forecast = self.data_handler.extract_forecasted_values(ticker, last_date, data)
        forecast["Date"] = pd.date_range(start=last_date + timedelta(days=1), periods=len(forecast))

        combined_df = pd.concat([
            data[["Date", "Actual", "Predicted"]],
            forecast[["Date", "Forecasted"]]
        ], ignore_index=True).sort_values("Date")

        fig = self.graph_generator.generate_actual_predicted_forecast_graph(combined_df, company, model)
        text = self.generate_single_stock_summary(company, data, forecast, model)
        return {"text": text, "graphs": [fig]}

    def _handle_compare_intent(self, intent_data):
        companies = intent_data["companies"]
        tickers = [self.intent_detector.resolve_ticker(name.upper()) + ".TA" for name in companies]
        ticker_to_company = {v: k for k, v in self.data_handler.ticker_mapping.items()}

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 3, 13)
        best_model_df = pd.read_csv(self.data_handler.best_model_path)

        combined_dataframes = []
        summaries = []

        for ticker in tickers:
            try:
                model = best_model_df.loc[best_model_df["Company"] == ticker, "Model"].values[0]
                data = self.data_handler.extract_by_model(ticker, model, start_date, end_date)
                last_date = data["Date"].max()
                forecast = self.data_handler.extract_forecasted_values(ticker, last_date, data)
                forecast["Date"] = pd.date_range(start=last_date + timedelta(days=1), periods=len(forecast))

                combined = pd.concat([
                    data[["Date", "Actual", "Predicted"]],
                    forecast[["Date", "Forecasted"]]
                ], ignore_index=True).sort_values("Date")

                combined_dataframes.append((ticker, model, combined))
                summaries.append(self.generate_single_stock_summary(ticker_to_company.get(ticker.replace(".TA", ""), ticker), data, forecast, model))
            except:
                continue

        if not combined_dataframes:
            return {"text": "No valid data found for comparison."}

        fig = self.graph_generator.generate_comparison_graph(combined_dataframes, ticker_to_company)
        summary = self.generate_comparison_summary(summaries)
        return {"text": summary, "graphs": [fig]}

    # =============================
    # Summary Generators
    # =============================

    def generate_sector_summary(self, actual_df, predicted_df, forecast_df, name_map, sector):
        def summarize(df, col):
            summary = []
            for ticker in df["Ticker"].unique():
                sub = df[df["Ticker"] == ticker]
                company = name_map.get(ticker.replace(".TA", ""), ticker)
                min_, max_, mean_ = sub[col].min(), sub[col].max(), sub[col].mean()
                trend = "upward" if sub[col].iloc[-1] > sub[col].iloc[0] else "downward"
                summary.append(f"- {company}: Min={min_:.2f}, Max={max_:.2f}, Mean={mean_:.2f}, Trend={trend}")
            return "\n".join(summary)

        input_text = (
            f"Sector-wide analysis for {sector} sector:\n\n"
            f"Actual:\n{summarize(actual_df, 'Actual')}\n\n"
            f"Predicted:\n{summarize(predicted_df, 'Predicted')}\n\n"
            f"Forecasted:\n{summarize(forecast_df, 'Forecasted')}\n\n"
            "Please analyze the sector's stock performance trends and give insights and future expectations."
        )
        return self.model.generate_content(input_text).text

    def generate_single_stock_summary(self, company, data, forecast_df, model):
        start = data["Date"].min().strftime("%Y-%m-%d")
        end = data["Date"].max().strftime("%Y-%m-%d")

        def stats(col):
            return {
                "min": data[col].min(),
                "max": data[col].max(),
                "mean": data[col].mean(),
                "trend": "upward" if data[col].iloc[-1] > data[col].iloc[0] else "downward"
            }

        actual_stats = stats("Actual")
        pred_stats = stats("Predicted")
        forecast_stats = {
            "min": forecast_df["Forecasted"].min(),
            "max": forecast_df["Forecasted"].max(),
            "mean": forecast_df["Forecasted"].mean(),
            "trend": "upward" if forecast_df["Forecasted"].iloc[-1] > forecast_df["Forecasted"].iloc[0] else "downward"
        }

        input_text = (
            f"Stock analysis for {company}:\n"
            f"Model used: {model}\n"
            f"Date range: {start} to {end}\n\n"
            f"Actual: Min={actual_stats['min']:.2f}, Max={actual_stats['max']:.2f}, Mean={actual_stats['mean']:.2f}, Trend={actual_stats['trend']}\n"
            f"Predicted: Min={pred_stats['min']:.2f}, Max={pred_stats['max']:.2f}, Mean={pred_stats['mean']:.2f}, Trend={pred_stats['trend']}\n"
            f"Forecasted: Min={forecast_stats['min']:.2f}, Max={forecast_stats['max']:.2f}, Mean={forecast_stats['mean']:.2f}, Trend={forecast_stats['trend']}\n\n"
            f"Please provide a summary of the stock performance and expected future trend."
        )

        return self.model.generate_content(input_text).text

    def generate_comparison_summary(self, summaries: list) -> str:
        input_text = (
            "Comparison of multiple stocks:\n\n"
            + "\n\n".join(summaries)
            + "\n\nCompare their trends, predictions, and forecasts. Highlight top performers."
        )
        return self.model.generate_content(input_text).text
