import pandas as pd
import numpy as np
import os
import pickle
from datetime import timedelta
import ast

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
        company_data["y_test"] = ast.literal_eval(company_data["y_test"])
        company_data["y_pred"] = ast.literal_eval(company_data["y_pred"])

        fixed_start = pd.to_datetime("2024-07-04")
        fixed_end = pd.to_datetime("2024-12-30")
        total_days = (fixed_end - fixed_start).days + 1  # inclusive

        # Truncate or pad values if necessary to fit range
        y_test = company_data["y_test"][:total_days]
        y_pred = company_data["y_pred"][:total_days]

        if len(y_test) < total_days:
            # pad with last value
            y_test += [y_test[-1]] * (total_days - len(y_test))
        if len(y_pred) < total_days:
            y_pred += [y_pred[-1]] * (total_days - len(y_pred))

        date_range = pd.date_range(start=fixed_start, end=fixed_end)

        actual_df = pd.DataFrame({"Date": date_range, "Actual": y_test})
        predicted_df = pd.DataFrame({"Date": date_range, "Predicted": y_pred})

        return pd.merge(actual_df, predicted_df, on="Date")


    def extract_by_industry(self, industry, start_date, end_date):
        df = pd.read_csv(self.sector_path)
        best_models = pd.read_csv(self.best_model_path)
        reverse_map = {v: k for k, v in self.ticker_mapping.items()}

        df.rename(columns={"Symbol": "Ticker"}, inplace=True)
        industry_companies = df[df["Industry"].str.lower() == industry.lower()]
        tickers = industry_companies["Ticker"].tolist()

        result = []

        for t in tickers:
            full_ticker = f"{t}.TA"
            try:
                model = best_models.loc[best_models["Company"] == full_ticker, "Model"].values[0]
                ap_df = self.extract_by_model(full_ticker, model, start_date, end_date)
                if ap_df.empty:
                    continue

                last_date = ap_df["Date"].max()
                forecast_df = self.extract_forecasted_values(full_ticker, last_date, ap_df)

                merged = pd.merge(ap_df, forecast_df, on="Date", how="outer")
                merged["Ticker"] = full_ticker
                merged["Industry"] = industry
                result.append(merged)
            except Exception as e:
                continue

        return pd.concat(result, ignore_index=True) if result else pd.DataFrame()


    def get_industry_actuals(self, industry, start_date, end_date):
        df = pd.read_csv(self.sector_path)

        # Normalize column names just in case
        df.rename(columns={"Symbol": "Ticker"}, inplace=True)

        # Filter companies in industry
        industry_companies = df[df["Industry"].str.lower() == industry.lower()]
        tickers = industry_companies["Ticker"].tolist()

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

    def get_industry_predictions(self, industry, start_date, end_date):
        df = pd.read_csv(self.sector_path)
        best_models = pd.read_csv(self.best_model_path)

        # Normalize column names
        df.rename(columns={"Symbol": "Ticker"}, inplace=True)
        reverse_map = {v: k for k, v in self.ticker_mapping.items()}

        # Filter companies in industry
        industry_companies = df[df["Industry"].str.lower() == industry.lower()]
        tickers = industry_companies["Ticker"].tolist()

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
            "LSTM": os.path.join("LSTM", "forecast_lstm_without_reports.csv"),
            "GRU": os.path.join("GRU", "forecast_gru_without_reports.csv"),
            "LightGBM": os.path.join("LightGBM", "model_LightGBM_metrics_and_predictions_total.csv"),
            "XGBoost": os.path.join("XGBoost", "model_XGBoost_metrics_and_predictions_without_report_parameters.csv")
        }
        best_model_df = pd.read_csv(self.best_model_path, encoding='latin-1')
        model = best_model_df.loc[best_model_df["Company"] == stock, "Model"].values[0]
        path = forecast_paths.get(model)

        if not path:
            raise ValueError(f"No forecast file for model: {model}")

        df = pd.read_csv(path, encoding='latin-1')
        if model in ["LSTM", "GRU"]:
            df = df[df["Ticker"] == stock][["Date", "Forecast"]]
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        else:
            df = df[df["Stock"] == stock]
            if df.empty:
                raise ValueError(f"No forecast data found for stock: {stock}")
        
            # Extract forecast columns (e.g., Day_1, Day_2, ...)
            forecast_cols = [col for col in df.columns if col.startswith("Day_")]
        
            # Reshape from wide to long
            df_melted = df.melt(value_vars=forecast_cols, value_name="Forecast", var_name="Day")
        
            # Extract numeric day offset
            df_melted["Day"] = df_melted["Day"].str.extract(r"Day_(\d+)").astype(int)
        
            # Generate actual forecast dates
            df_melted["Date"] = [last_predicted_date + timedelta(days=int(x)) for x in df_melted["Day"]]
        
            # Finalize forecast DataFrame
            df = df_melted[["Date", "Forecast"]].sort_values("Date").reset_index(drop=True)


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
