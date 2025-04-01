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
from copy import deepcopy

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from intent_detector import IntentDetector
from stock_data_handler import StockDataHandler
from graph_generator import GraphGenerator
from chatbot_engine import ChatbotEngine

warnings.filterwarnings("ignore")

# Global Configuration
API_KEY = 'AIzaSyCTNncuxKui7XIzrZWt1o_EtLIxiew8qtE'
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"
LSTM_CSV_PATH = "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm.csv"
XGBOOST_CSV_PATH = "/workspaces/FinalProj/XGBoost/model_XGBoost_metrics_and_predictions.csv"
LIGHTGBM_CSV_PATH = "/workspaces/FinalProj/LightGBM/LightGBM_metrics_and_predictions.csv"
BEST_MODEL_CSV = "/workspaces/FinalProj/Metrics/without_ARIMA_model_to_stock.csv"
SECTORS_DF_PATH = "sectors_df.csv"

if "mentioned_tickers" not in st.session_state:
    st.session_state.mentioned_tickers = set()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

class AppManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", API_KEY)
        self.model = self.initialize_model()
        self.ticker_mapping = self.load_ticker_mapping()
        self.industry_mapping = self.load_industry_mapping()
        self.intent_detector = IntentDetector(self.ticker_mapping, self.industry_mapping)
        self.model_paths = {
            "LSTM": LSTM_CSV_PATH,
            "GRU": "/workspaces/FinalProj/GRU/actual_vs_pred_gru.csv",
            "XGBoost": XGBOOST_CSV_PATH,
            "LightGBM": LIGHTGBM_CSV_PATH,
        }

        self.data_handler = StockDataHandler(
            self.ticker_mapping,
            model_paths=self.model_paths,
            sector_path=SECTORS_DF_PATH,
            best_model_path=BEST_MODEL_CSV
        )

        self.graph_generator = GraphGenerator()
        self.engine = ChatbotEngine(self.data_handler, self.graph_generator, self.intent_detector)

    def initialize_model(self):
        genai.configure(api_key=self.api_key)
        return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash-8b",
                    temperature=0.3,
                    google_api_key=self.api_key
                )

    def load_ticker_mapping(self) -> dict:
        df = pd.read_excel(MAPPING_FILE_PATH)
        return {row["CompanyName"].upper(): row["Ticker"].upper() for _, row in df.iterrows()}
    def load_industry_mapping(self) -> dict:
        """
        Loads industry names from the sectors CSV and creates a mapping from
        cleaned variations to canonical industry names.
        """
        df = pd.read_csv(SECTORS_DF_PATH)
        df = df.dropna(subset=["Industry"])
        canonical_industries = df["Industry"].unique()

        industry_mapping = {}

        for industry in canonical_industries:
            cleaned = (
                str(industry).lower()
                .replace("-", " ")
                .replace(":", " ")
                .replace("_", " ")
                .replace(",", " ")
            )
            cleaned = " ".join(cleaned.split())  # normalize spaces
            industry_mapping[cleaned] = industry.strip()

        return industry_mapping


    def run(self):
        st.set_page_config(page_title="Robo Advisor", layout="wide")
        st.title("🤖 Robo Advisor – Israeli Stock Market")

        st.sidebar.title("About")
        st.sidebar.info("This chatbot provides stock analysis using historical and forecasted data.")

        # Display previous messages
        for message in st.session_state.chat_history:
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.write(message.content)
            elif isinstance(message, dict) and message.get("role") == "assistant":
                with st.chat_message("assistant"):
                    for graph in message.get("graphs", []):
                        st.plotly_chart(graph, use_container_width=True)
                    if message.get("text"):
                        st.markdown(message["text"])
            elif isinstance(message, AIMessage):  # fallback for old messages
                with st.chat_message("assistant"):
                    st.write(message.content)



        # Handle new user input
        if prompt := st.chat_input("What would you like to know?"):
            user_msg = HumanMessage(content=prompt)
            st.session_state.chat_history.append(user_msg)
            with st.chat_message("user"):
                st.write(prompt)

            # FIRST: Try intent-based response
            structured_response = self.engine.handle_input(prompt)
            if "text" in structured_response or "graphs" in structured_response:
                with st.chat_message("assistant"):
                    if "graphs" in structured_response:
                        for graph in structured_response["graphs"]:
                            st.plotly_chart(graph, use_container_width=True)
                    if "text" in structured_response:
                        st.markdown(structured_response["text"])

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "text": structured_response.get("text", ""),
                    "graphs": structured_response.get("graphs", [])
                })
                return  # ✅ End here if intent handled

            # SECOND: fallback to Gemini via LangChain
            conversation_history = "\n".join([
                f"User: {m.content}" if isinstance(m, HumanMessage)
                else f"Assistant: {m.content}" if isinstance(m, AIMessage)
                else f"Assistant: {m.get('text', '')}" if isinstance(m, dict) and m.get("role") == "assistant"
                else ""
                for m in st.session_state.chat_history
            ])

            def get_response(user_query, conversation_history):
                prompt_template = """
                You are a helpful assistant specialized in Israeli stock market data. If no intent is detected, answer naturally.
                note that there will be typos, so correct them.
                Your users are new to the stock market, soo not only present data and graph, but explain deeply

                Chat history:
                {conversation_history}

                User question:
                {user_query}
                """
                prompt = ChatPromptTemplate.from_template(prompt_template)
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    temperature=0.3,
                    google_api_key=self.api_key,
                    stream=True
                )
                chain = prompt | llm | StrOutputParser()
                return chain.stream({
                    "conversation_history": conversation_history,
                    "user_query": user_query
                })

            # Stream Gemini response
            stream = get_response(prompt, conversation_history)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()  # Reserve a spot for streamed text
                full_response = ""

                for chunk in stream:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")  # Typing cursor effect

                message_placeholder.markdown(full_response)  # Final clean output

            # ✅ Save Gemini response correctly to history
            st.session_state.chat_history.append(AIMessage(content=full_response))



if __name__ == "__main__":
    app = AppManager()
    app.run()

