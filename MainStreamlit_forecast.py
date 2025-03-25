import streamlit as st
from GraphDrawer import GraphDrawer
import google.generativeai as genai
import matplotlib.pyplot as plt
from io import BytesIO
import os
import pandas as pd
import base64
import pickle
import numpy as np
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import plotly.graph_objects as go
import warnings
import time
import emoji

warnings.filterwarnings("ignore")

# Global Configuration
API_KEY = 'AIzaSyCTNncuxKui7XIzrZWt1o_EtLIxiew8qtE'
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"
LSTM_CSV_PATH = "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm.csv"
XGBOOST_CSV_PATH = "/workspaces/FinalProj/XGBoost/model_XGBoost_metrics_and_predictions.csv"
LIGHTGBM_CSV_PATH = "/workspaces/FinalProj/LightGBM/LightGBM_metrics_and_predictions.csv"
BEST_MODEL_CSV = "/workspaces/FinalProj/Metrics/without_ARIMA_model_to_stock.csv"
SECTORS_DF_PATH = "sectors_df.csv"
# Initialize API and Streamlit

if "mentioned_tickers" not in st.session_state:
    st.session_state.mentioned_tickers = set()

def initialize_data():
    return pd.read_csv(LSTM_CSV_PATH)


class IntentDetector:
    def __init__(self, ticker_mapping):
        self.ticker_mapping = ticker_mapping

    def detect(self, user_input: str) -> dict:
        """
        Detects the user's intent from text.
        """
        user_input = user_input.lower()

        # Sector intent
        sector_keywords = ["actual values", "sector", "companies in sector", "all"]
        if any(keyword in user_input for keyword in sector_keywords):
            sector_name = user_input.split("sector")[1].strip() if "sector" in user_input else None
            if sector_name:
                return {"intent": "sector_values", "sector": sector_name}
            raise ValueError("Please specify the sector name for the query.")

        # Comparison intent
        compare_keywords = ["compare", "comparison", "difference between", "versus",
                            "vs", ",", "&", "and", "compare me the stocks of", "with"]
        if any(keyword in user_input for keyword in compare_keywords):
            return {"intent": "compare", "companies": self.extract_company_names(user_input)}

        # Single stock graph
        graph_keywords = ["graph", "plot", "visualize", "show", "chart of", "chart", "plot of", "graph of"]
        if any(keyword in user_input for keyword in graph_keywords):
            if "compare" in user_input or ("and" in user_input or "," in user_input):
                return {"intent": "compare", "companies": self.extract_company_names(user_input)}
            else:
                return {"intent": "graph", "company": self.extract_company_name(user_input)}

        return {"intent": "text"}

    def extract_company_name(self, user_input: str) -> str:
        """
        Extracts a single company name for graphing.
        """
        user_input = user_input.lower()
        graph_keywords = ["graph of", "graph", "plot of", "plot", "visualize", "show", "chart of", "chart"]

        for keyword in graph_keywords:
            if keyword in user_input:
                return user_input.split(keyword)[-1].strip()

        raise ValueError("No recognizable company name in input.")

    def extract_company_names(self, user_input: str) -> list:
        """
        Extracts multiple company names for comparison.
        """
        user_input = user_input.lower()
        delimiters = ["compare", "comparison", "difference between", "versus", "vs",
                      ",", "&", "and", "compare me the stocks of", "with"]

        for delimiter in delimiters:
            user_input = user_input.replace(delimiter, ",")

        companies = [c.strip() for c in user_input.split(",") if c.strip()]
        words_list = []
        for company in companies:
            words_list += company.split()

        valid_companies = []
        for company in words_list:
            for valid_name in self.ticker_mapping.keys():
                if valid_name in company.upper():
                    valid_companies.append(valid_name)
                    break

        if len(valid_companies) < 2:
            raise ValueError("At least two valid companies are required for comparison.")

        return list(set(valid_companies))

    def resolve_ticker(self, user_input: str) -> str:
        """
        Maps a company name or ticker to the actual ticker symbol.
        """
        user_input = user_input.strip().upper()
        for company_name, ticker in self.ticker_mapping.items():
            if user_input in company_name or user_input == ticker:
                return ticker
        raise ValueError(f"Ticker or company name '{user_input}' not found in mapping.")

# Extract Data by Model

class StockDataHandler:
    def __init__(self, ticker_mapping, model_paths: dict, sector_path: str, best_model_path: str):
        self.ticker_mapping = ticker_mapping
        self.model_paths = model_paths
        self.sector_path = sector_path
        self.best_model_path = best_model_path

    def extract_by_model(self, ticker: str, model: str, start_date, end_date):
        if model not in self.model_paths and model != "ARIMA":
            raise ValueError(f"Unsupported model: {model}")

        if model == "ARIMA":
            return self._load_arima_data(ticker, start_date, end_date)

        df = pd.read_csv(self.model_paths[model])

        if model in ["LSTM", "GRU"]:
            return self._filter_stock_data(df, ticker, start_date, end_date)
        elif model in ["XGBoost", "LightGBM"]:
            company_data = df[df["Stock"] == ticker].iloc[0]
            return self._process_model_data(company_data, start_date)

        raise ValueError(f"Unhandled model: {model}")

    def _filter_stock_data(self, df, ticker, start_date, end_date):
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        ticker = ticker if ticker.endswith(".TA") else f"{ticker}.TA"
        return df[(df["Ticker"] == ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]


    def _process_model_data(self, company_data, start_date):
        company_data["y_test"] = eval(company_data["y_test"])
        company_data["y_pred"] = eval(company_data["y_pred"])

        actual_df = pd.DataFrame({
            "Date": pd.date_range(start=start_date, periods=len(company_data["y_test"])),
            "Actual": company_data["y_test"]
        })
        predicted_df = pd.DataFrame({
            "Date": pd.date_range(start=start_date, periods=len(company_data["y_pred"])),
            "Predicted": company_data["y_pred"]
        })
        return pd.merge(actual_df, predicted_df, on="Date")

    def _load_arima_data(self, ticker, start_date, end_date):
        rev_map = {v: k for k, v in self.ticker_mapping.items()}
        stripped_ticker = ticker.replace(".TA", "")
        company_name = rev_map.get(stripped_ticker)

        if not company_name:
            raise ValueError(f"No company name found for {ticker}")

        normalized_name = company_name.strip().upper()
        actual_path = f"/workspaces/FinalProj/ARIMA/Actuals/{normalized_name}_actuals.pkl"
        predicted_path = f"/workspaces/FinalProj/ARIMA/Predictions/{normalized_name}_predictions.pkl"

        if not os.path.exists(actual_path) or not os.path.exists(predicted_path):
            raise FileNotFoundError(f"Missing ARIMA files for {normalized_name}")

        with open(actual_path, "rb") as f:
            actual = pickle.load(f)
        with open(predicted_path, "rb") as f:
            predicted = pickle.load(f)

        if isinstance(actual, np.ndarray):
            actual = pd.Series(actual, name="Actual")
        if isinstance(predicted, np.ndarray):
            predicted = pd.Series(predicted, name="Predicted")

        if not isinstance(actual.index, pd.DatetimeIndex):
            actual.index = pd.date_range(start=start_date, periods=len(actual))
        if not isinstance(predicted.index, pd.DatetimeIndex):
            predicted.index = pd.date_range(start=start_date, periods=len(predicted))

        df_actual = pd.DataFrame({"Date": actual.index, "Actual": actual.values})
        df_pred = pd.DataFrame({"Date": predicted.index, "Predicted": predicted.values})

        merged = pd.merge(df_actual, df_pred, on="Date")
        merged["Date"] = pd.to_datetime(merged["Date"], dayfirst=True)
        return merged[(merged["Date"] >= start_date) & (merged["Date"] <= end_date)]

    def get_sector_actuals(self, sector, start_date, end_date):
        df = pd.read_csv(self.sector_path)

        # Normalize column names just in case
        df.rename(columns={"Symbol": "Ticker"}, inplace=True)

        # Filter companies in sector
        sector_companies = df[df["Market Sector"].str.lower() == sector.lower()]
        tickers = sector_companies["Ticker"].tolist()

        result = []

        for t in tickers:
            full_ticker = f"{t}.TA"
            try:
                data = self.extract_by_model(full_ticker, "LSTM", start_date, end_date)
                if not data.empty:
                    result.append(pd.DataFrame({
                        "Ticker": full_ticker,
                        "Date": data["Date"],
                        "Actual": data["Actual"]
                    }))
            except Exception as e:
                continue  # Could log this

        return pd.concat(result, ignore_index=True) if result else pd.DataFrame()

    def get_sector_predictions(self, sector, start_date, end_date):
        df = pd.read_csv(self.sector_path)
        best_models = pd.read_csv(self.best_model_path)

        # Normalize column names
        df.rename(columns={"Symbol": "Ticker"}, inplace=True)
        reverse_map = {v: k for k, v in self.ticker_mapping.items()}

        # Filter companies in sector
        sector_companies = df[df["Market Sector"].str.lower() == sector.lower()]
        tickers = sector_companies["Ticker"].tolist()

        result = []

        for t in tickers:
            full_ticker = f"{t}.TA"
            try:
                model = best_models.loc[best_models["Company"] == full_ticker, "Model"].values[0]
                data = self.extract_by_model(full_ticker, model, start_date, end_date)
                if not data.empty:
                    company_name = reverse_map.get(t, t)
                    result.append(pd.DataFrame({
                        "Ticker": full_ticker,
                        "Date": data["Date"],
                        "Predicted": data["Predicted"],
                        "Company": company_name
                    }))
            except Exception as e:
                continue

        return pd.concat(result, ignore_index=True) if result else pd.DataFrame()


    def extract_forecasted_values(self, stock, last_predicted_date, actual_predicted: pd.DataFrame):
        
        forecast_paths = {
            "LSTM": "/workspaces/FinalProj/LSTM/forecast_lstm.csv",
            "GRU": "/workspaces/FinalProj/GRU/forecast_gru.csv",
            "LightGBM": "/workspaces/FinalProj/LightGBM/LightGBM_forecast_stocks.csv",
            "XGBoost": "/workspaces/FinalProj/XGBoost/XGBoost_forecast_stocks.csv"
        }
        best_model_df = pd.read_csv(self.best_model_path)
        model = best_model_df.loc[best_model_df["Company"] == stock, "Model"].values[0]
        path = forecast_paths.get(model)

        if not path:
            raise ValueError(f"No forecast file for model: {model}")

        df = pd.read_csv(path)
        if model in ["LSTM", "GRU"]:
            df = df[df["Ticker"] == stock][["Date", "Forecast"]]
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        else:
            df = df[df["Ticker"] == stock][["Day", "Forecast"]]
            df["Day"] = df["Day"].str.extract(r"Day_(\d+)").astype(int)
            df["Date"] = [last_predicted_date + timedelta(days=int(x)) for x in df["Day"].iloc[:, 0]]
            df.drop(columns="Day", inplace=True)

        # Adjust forecast to start from last predicted value
        last_pred = actual_predicted.loc[actual_predicted["Date"] == last_predicted_date, "Predicted"].values[0]
        adjustment = last_pred - df["Forecast"].iloc[0]
        df["Forecasted"] = df["Forecast"] + adjustment
        df.drop(columns="Forecast", inplace=True)

        return df
    @staticmethod
    def synchronize_x_axis(dataframes: list) -> list:
        """
        Aligns multiple DataFrames to a shared x-axis (date range).
        Forward-fills missing data.
        """
        if not dataframes:
            return []

        all_dates = pd.concat([df['Date'] for df in dataframes])
        unified_range = pd.date_range(start=all_dates.min(), end=all_dates.max())

        synchronized = []
        for df in dataframes:
            df = df.set_index('Date').reindex(unified_range).reset_index()
            df.rename(columns={'index': 'Date'}, inplace=True)
            df.fillna(method='ffill', inplace=True)
            synchronized.append(df)

        return synchronized


import plotly.graph_objects as go
import pandas as pd

class GraphGenerator:
    def __init__(self):
        pass

    def generate_actual_predicted_forecast_graph(self, df: pd.DataFrame, stock: str, model: str):
        """
        Generates a full line chart for Actual, Predicted, and Forecasted data.
        """
        fig = go.Figure()

        if "Actual" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode='lines', name='Actual',
                line=dict(color='blue', width=2)
            ))

        if "Predicted" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode='lines', name='Predicted',
                line=dict(color='orange', width=2, dash='dash')
            ))

        if "Forecasted" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Forecasted"],
                mode='lines', name='Forecasted',
                line=dict(color='green', width=2, dash='dot')
            ))

        fig.update_layout(
            title=f"Actual, Predicted, and Forecasted Values for {stock} ({model})",
            xaxis_title="Date",
            yaxis_title="Value",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_xaxes(tickformat='%Y-%m', tickangle=45, showgrid=True)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_sector_graph(self, df: pd.DataFrame, value_column: str, sector_name: str):
        """
        Plots all companies in a sector using the specified column (Actual or Predicted).
        """
        fig = go.Figure()
        for company, group in df.groupby("Company" if "Company" in df else "Ticker"):
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(group["Date"], dayfirst=True),
                y=group[value_column],
                mode='lines',
                name=company
            ))

        fig.update_layout(
            title=f"{value_column} Values for {sector_name} Sector",
            xaxis_title="Date",
            yaxis_title=value_column,
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_xaxes(tickformat='%b %d, %Y', dtick=50 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_comparison_graph(self, dataframes: list, ticker_to_company_name: dict):
        """
        Plots multiple companies with actual, predicted, and forecasted lines.
        `dataframes`: list of (ticker, model, combined_df)
        """
        fig = go.Figure()
        for ticker, model, df in dataframes:
            name = ticker_to_company_name.get(ticker.replace(".TA", ""), ticker)

            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode='lines',
                name=f"{name} Actual ({model})",
                line=dict(dash='solid')
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode='lines',
                name=f"{name} Predicted ({model})",
                line=dict(dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Forecasted"],
                mode='lines',
                name=f"{name} Forecasted ({model})",
                line=dict(dash='dot')
            ))

        fig.update_layout(
            title="Stock Price Comparison",
            xaxis_title="Date",
            yaxis_title="Price",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(tickformat='%Y-%m', tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def customize(self, fig):
        """
        Applies a consistent theme to the plot.
        """
        fig.update_layout(
            plot_bgcolor="#F9F6E6",
            font=dict(family="Arial, sans-serif", size=15, color="#333333"),
            colorway=["#001219", "#005f73", "#0a9396", "#94d2bd", "#ee9b00", "#ca6702", "#bb3e03", "#9b2226"],
            hoverlabel=dict(font_size=16),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14)),
        )
        return fig

    def synchronize_and_plot_lstm_adjusted_comparison(self, dataframes, company_models: dict, title: str):
        """
        Synchronize time ranges across models (handling LSTM/GRU specially),
        then plot a comparative graph.
        """
        # Determine full date range
        all_dates = pd.concat([df["Date"] for _, _, df in dataframes])
        start_date, end_date = all_dates.min(), all_dates.max()

        fig = go.Figure()

        for ticker, model, df in dataframes:
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

            if model in ["LSTM", "GRU"]:
                # Extend backwards with first Actual value
                first_date = df["Date"].iloc[0]
                first_value = df["Actual"].iloc[0]
                backfill_dates = pd.date_range(start=start_date, end=first_date - pd.Timedelta(days=1))

                extended_df = pd.DataFrame({"Date": backfill_dates, "Actual": first_value})
                df = pd.concat([extended_df, df], ignore_index=True)

                # Cut off future dates
                df = df[df["Date"] <= end_date]
            else:
                # Truncate to range
                df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

            name = ticker.replace(".TA", "")
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode="lines", name=f"{name} Actual ({model})",
                line=dict(dash="solid")
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode="lines", name=f"{name} Predicted ({model})",
                line=dict(dash="dash")
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickformat="%Y-%m", dtick=30 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)

        return self.customize(fig)

# Chatbot Response Logic
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


def text_streamer(text, delay=0.03):
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)
import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import time
from copy import deepcopy

class AppManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", API_KEY)
        self.model = self.initialize_model()
        self.ticker_mapping = self.load_ticker_mapping()

        # Init subcomponents
        self.intent_detector = IntentDetector(self.ticker_mapping)

        self.model_paths = {
            "LSTM": "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm.csv",
            "GRU": "/workspaces/FinalProj/GRU/actual_vs_pred_gru.csv",
            "XGBoost": "/workspaces/FinalProj/XGBoost/model_XGBoost_metrics_and_predictions.csv",
            "LightGBM": "/workspaces/FinalProj/LightGBM/LightGBM_metrics_and_predictions.csv",
        }

        self.data_handler = StockDataHandler(
            self.ticker_mapping,
            model_paths=self.model_paths,
            sector_path="sectors_df.csv",
            best_model_path="/workspaces/FinalProj/Metrics/without_ARIMA_model_to_stock.csv"
        )

        self.graph_generator = GraphGenerator()
        self.engine = ChatbotEngine(self.model, self.data_handler, self.graph_generator, self.intent_detector)

    def initialize_model(self):
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash-8b",
            system_instruction="You are a chatbot for analyzing Israeli stock market data. Be helpful, smart, and polite."
        )

    def load_ticker_mapping(self) -> dict:
        df = pd.read_excel("company_name_to_ticker.xlsx")
        return {row["CompanyName"].upper(): row["Ticker"].upper() for _, row in df.iterrows()}

    def run(self):
        st.set_page_config(page_title="Robo Advisor", layout="wide")
        st.title("🤖 Robo Advisor – Israeli Stock Market")

        st.sidebar.title("About")
        st.sidebar.info("This chatbot provides stock analysis using historical and forecasted data.")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "mentioned_tickers" not in st.session_state:
            st.session_state.mentioned_tickers = set()

        # Display chat history
        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                if "graphs" in msg:
                    for j, graph in enumerate(msg["graphs"]):
                        st.plotly_chart(graph, use_container_width=True, key=f"history_{i}_{j}")
                if "content" in msg:
                    st.markdown(msg["content"])

        # Handle input
        if prompt := st.chat_input("What would you like to know?"):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            response = self.engine.handle_input(prompt)

            with st.chat_message("assistant"):
                if "graphs" in response:
                    for j, graph in enumerate(response["graphs"]):
                        st.plotly_chart(graph, use_container_width=True, key=f"response_{len(st.session_state.chat_history)}_{j}")
                        time.sleep(1)

                if "text" in response:
                    st.write_stream(self.stream_response_text(response["text"]))

            # Save response in history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.get("text", ""),
                "graphs": [deepcopy(graph) for graph in response.get("graphs", [])]
            })

    def stream_response_text(self, text, delay=0.03):
        for word in text.split(" "):
            yield word + " "
            time.sleep(delay)
             



if __name__ == "__main__":
    app = AppManager()
    app.run()

