import pandas as pd
import numpy as np
import os
import pickle
from datetime import timedelta


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
