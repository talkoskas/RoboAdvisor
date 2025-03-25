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
import google.generativeai as genai
import time
from copy import deepcopy
warnings.filterwarnings("ignore")

#import modules:
from intent_detector import IntentDetector
from stock_data_handler import StockDataHandler
from graph_generator import GraphGenerator
from chatbot_engine import ChatbotEngine


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

def text_streamer(text, delay=0.03):
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)


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

