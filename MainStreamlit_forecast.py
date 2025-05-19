import streamlit as st
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
import uuid
from copy import deepcopy
from chatbot_engine import ChatbotEngine

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from intent_detector import IntentDetector
from stock_data_handler import StockDataHandler
from graph_generator import GraphGenerator

warnings.filterwarnings("ignore")

# Global Configuration
API_KEY = 'AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI'
LSTM_CSV_PATH = os.path.join("LSTM", "actual_vs_pred_lstm_without_reports.csv")
XGBOOST_CSV_PATH = os.path.join("XGBoost", "model_XGBoost_metrics_and_predictions_without_report_parameters.csv")
LIGHTGBM_CSV_PATH = os.path.join("LightGBM", "model_LightGBM_metrics_and_predictions_total.csv")
BEST_MODEL_CSV = os.path.join("Metrics", "without_ARIMA_model_to_stock.csv")
SECTORS_DF_PATH = "sectors_df.csv"
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"

if "mentioned_tickers" not in st.session_state:
    st.session_state.mentioned_tickers = set()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

class AppManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", API_KEY)
        self.ticker_mapping = self.load_ticker_mapping()
        self.industry_mapping = self.load_industry_mapping()
        self.intent_detector = IntentDetector(self.ticker_mapping, self.industry_mapping)
        self.model_paths = {
            "LSTM": LSTM_CSV_PATH,
            "GRU": os.path.join("GRU", "actual_vs_pred_gru_without_reports.csv"),
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

    def load_ticker_mapping(self) -> dict:
        df = pd.read_excel(MAPPING_FILE_PATH)
        return {row["CompanyName"].upper(): row["Ticker"].upper() for _, row in df.iterrows()}

    def load_industry_mapping(self) -> dict:
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
            cleaned = " ".join(cleaned.split())
            industry_mapping[cleaned] = industry.strip()
        return industry_mapping

    def run(self):
        def get_clean_chat_history():
            lines = []
            for m in st.session_state.chat_history:
                if isinstance(m, HumanMessage):
                    lines.append(f"User: {m.content}")
                elif isinstance(m, AIMessage):
                    lines.append(f"Assistant: {m.content}")
                elif isinstance(m, dict):
                    if m.get("role") == "assistant":
                        if "deep_analysis" in m:
                            lines.append(f"Assistant: {m['deep_analysis']}")
                        elif "text" in m:
                            lines.append(f"Assistant: {m['text']}")
                    elif m.get("role") == "user" and "text" in m:
                        lines.append(f"User: {m['text']}")
            return "\n".join(lines)

        if "accepted_disclaimer" not in st.session_state:
            st.session_state.accepted_disclaimer = False

        if not st.session_state.accepted_disclaimer:
            # ── INSERT A GREETING ─────────────────────────────────────────────────────────
            user = st.session_state.get("username", None)
            if user:
                st.markdown(f"### Hello, **{user}** 👋")
            st.title("🤖 Welcome to the Robo Advisor – Israeli Stock Market")

            st.markdown("## 📊 Stock Analysis and Forecasting Application")
            st.markdown("""
        This is a **Streamlit-based tool** that helps you analyze and forecast stock performance, especially for companies in the Israeli (TA) stock market.

        It combines **advanced machine learning models** like **LSTM**, **GRU**, **XGBoost** and **LightGBM** to deliver clear insights into stock behavior.

        Whether you're a student, investor, or just curious — this app makes stock analysis simple, visual, and accessible.
        """)

            st.markdown("## 🧠 What Can This App Do?")
            st.markdown("""
        - 📈 **Visualize actual vs predicted stock performance**
        - 🔮 **Forecast future trends using advanced models**
        - 🏭 **Explore industry-wide behavior across sectors**
        - ⚖️ **Compare multiple stocks side-by-side**
        - 🤖 **Interact with an AI chatbot** that answers your questions and generates graphs

        The chatbot uses **natural language processing** to understand your queries and provide visual + textual feedback.
        """)

            st.markdown("## ⚙️ How Does It Work?")
            st.markdown("""
        The app uses machine learning models to detect patterns in historical stock prices and predict future performance:

        - **LSTM / GRU** → sequence-aware models for time-series forecasting  
        - **XGBoost / LightGBM** → powerful tree-based models for structured tabular data  

        It visualizes **actual**, **predicted**, and **forecasted** data for each company or sector in interactive graphs.
        """)

            st.markdown("## 💬 How Do I Use It?")
            st.markdown("""
        You can ask the chatbot anything like:

        - 🟢 `show me the graph of leumi`
        - 🟢 `compare leumi and poalim`
        - 🟢 `show me all companies in industry Banks`

        The app will detect your intent and generate relevant insights and visuals.
        """)

            st.markdown("## 🎓 Academic Context")
            st.markdown("""
        This application was developed as part of a **Data Science Capstone Project** at **Ben-Gurion University (BGU)**, by students in the Department of Software and Information Systems Engineering.
        """)

            st.markdown("## ⚠️ Disclaimer")
            st.warning("""
        The chatbot's responses are **not binding financial recommendations** and do **not replace professional advice**.  
        All outputs are based on historical data and model estimations and are provided for educational purposes only.
        """)

            st.markdown("")

            if st.button("✅ I understand and wish to continue"):
                st.session_state.accepted_disclaimer = True
                st.rerun()

            return

        # st.set_page_config(page_title="Robo Advisor", layout="wide")

        # ── INSERT A GREETING ─────────────────────────────────────────────────────────
        user = st.session_state.get("username", None)
        if user:
            st.markdown(f"### Hello, **{user}** 👋")
        # ───────────────────────────────────────────────────────────────────────────────

        st.title("🤖 Robo Advisor – Israeli Stock Market")
        st.sidebar.title("About")
        st.sidebar.info("This chatbot provides stock analysis using historical and forecasted data.")

        # Default prompt buttons
        default_prompts = [
            "show me the graph of leumi",
            "compare leumi and poalim",
            "show me all companies in industry Banks"
        ]
        cols = st.columns(len(default_prompts))
        selected_prompt = None
        for i, p in enumerate(default_prompts):
            if cols[i].button(p, use_container_width=True):
                selected_prompt = p

        # Display chat history
        for message in st.session_state.chat_history:
            if isinstance(message, HumanMessage):
                with st.chat_message("user"): st.write(message.content)
            elif isinstance(message, dict) and message.get("role") == "assistant":
                with st.chat_message("assistant"):
                    for graph in message.get("graphs", []):
                        st.plotly_chart(graph, use_container_width=True, key=str(id(graph)))
                    if message.get("text"):
                        lang = st.session_state.get("language", "en")
                        align = "right" if lang == "he" else "left"
                        dir_attr = "rtl" if lang == "he" else "ltr"
                        st.markdown(
                            f'<div dir="{dir_attr}" style="text-align: {align}; font-size: 18px;">{message["text"]}</div>',
                            unsafe_allow_html=True
                        )
                    if message.get("deep_analysis"):
                        st.markdown("### 🔍 Deeper Analysis")
                        lang = st.session_state.get("language", "en")
                        align = "right" if lang == "he" else "left"
                        dir_attr = "rtl" if lang == "he" else "ltr"
                        st.markdown(
                            f'<div dir="{dir_attr}" style="text-align: {align}; font-size: 18px;">{message["deep_analysis"]}</div>',
                            unsafe_allow_html=True
                        )
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"): st.write(message.content)

        # User input
        manual_input = st.chat_input("What would you like to know?")
        prompt = selected_prompt or manual_input

        if prompt:
            # Language detection & append
            st.session_state["language"] = "he" if any('\u0590' <= c <= '\u05EA' for c in prompt) else "en"
            user_msg = HumanMessage(content=prompt)
            st.session_state.chat_history.append(user_msg)
            with st.chat_message("user"): st.write(prompt)

            # Generate and display summary + graphs
            structured_response = self.engine.handle_input(prompt)
            st.session_state["last_structured_response"] = structured_response
            with st.chat_message("assistant"):
                for i, graph in enumerate(structured_response.get("graphs", [])):
                    st.plotly_chart(graph, use_container_width=True, key=f"main_{i}_{uuid.uuid4()}")
                if structured_response.get("text"):
                    lang = st.session_state.get("language", "en")
                    align = "right" if lang == "he" else "left"
                    dir_attr = "rtl" if lang == "he" else "ltr"
                    st.markdown(
                        f'<div dir="{dir_attr}" style="text-align: {align}; font-size: 18px;">{structured_response["text"]}</div>',
                        unsafe_allow_html=True
                    )

            # Save summary to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "text": structured_response.get("text", ""),
                "graphs": structured_response.get("graphs", [])
            })

            # Schedule deeper analysis after each valid intent
            if structured_response.get("intent") in ["graph", "compare", "industry_values"]:
                st.session_state["deep_analysis_pending"] = {
                    "summary": structured_response["text"],
                    "context": f"{structured_response.get('intent').capitalize()} Analysis"
                }

        # Always show deeper-analysis buttons when pending
        if "deep_analysis_pending" in st.session_state:
            st.markdown("### 🔍 Would you like a deeper analysis?")
            c1, c2 = st.columns([1,1])
            if c1.button("🎨 Yes, show me!", use_container_width=True):
                with st.spinner("🔍 Generating deeper analysis..."):
                    pending = st.session_state.pop("deep_analysis_pending")
                    deep_result = self.engine._generate_deeper_analysis(
                        pending["summary"], context_info=pending["context"]
                    )
                    with st.chat_message("assistant"):
                        st.markdown("### 🔍 Deeper Analysis")
                        lang = st.session_state.get("language", "en")
                        align = "right" if lang == "he" else "left"
                        dir_attr = "rtl" if lang == "he" else "ltr"
                        st.markdown(
                            f'<div dir="{dir_attr}" style="text-align: {align}; font-size: 18px;">{deep_result}</div>',
                            unsafe_allow_html=True
                        )
                    st.session_state.chat_history.append({"role": "assistant", "deep_analysis": deep_result})
            if c2.button("❌ No thanks", use_container_width=True):
                st.session_state.pop("deep_analysis_pending", None)

if __name__ == "__main__":
    app = AppManager()
    app.run()
