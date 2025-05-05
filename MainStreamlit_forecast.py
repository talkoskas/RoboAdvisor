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
API_KEY = 'AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI'
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"
LSTM_CSV_PATH = "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm_without_reports.csv"
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
                    model="gemini-2.0-flash-lite",
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
        if "accepted_disclaimer" not in st.session_state:
         st.session_state.accepted_disclaimer = False

        if not st.session_state.accepted_disclaimer:
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
        - 🟢 `show me all companies in industry Banks - Regional`

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

            return  # prevent chatbot from rendering


        st.set_page_config(page_title="Robo Advisor", layout="wide")
        st.title("🤖 Robo Advisor – Israeli Stock Market")
        st.sidebar.title("About")
        st.sidebar.info("This chatbot provides stock analysis using historical and forecasted data.")

        # ✅ Always keep the button pills here (static location)
        default_prompts = [
            "show me the graph of leumi",
            "compare leumi and poalim",
            "show me all companies in industry Banks - Regional"
        ]

        cols = st.columns(len(default_prompts))
        selected_prompt = None
        for i, p in enumerate(default_prompts):
            if cols[i].button(p, use_container_width=True):
                selected_prompt = p

        # ✅ Show chat history below that
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
                    if message.get("deep_analysis"):
                        st.markdown("### 🔍 Deeper Analysis")
                        st.markdown(message["deep_analysis"])
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(message.content)

        # ✅ Always show chat input
        manual_input = st.chat_input("What would you like to know?")
        prompt = selected_prompt or manual_input

        if prompt:
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
                    # Trigger deeper Gemini analysis AFTER initial summary is shown
                if structured_response.get("intent") in ["graph", "compare", "industry_values"]:
                    with st.spinner("🔍 Generating deeper AI insights..."):
                        from chatbot_engine import get_llm_instance
                        from langchain_core.prompts import ChatPromptTemplate
                        from langchain_core.output_parsers import StrOutputParser

                        # Format graph summary if available
                        def summarize_graphs(graphs):
                            if not graphs:
                                return ""
                            return f"({len(graphs)} interactive visualizations attached – actual, predicted, forecasted trends shown per request.)"

                        # Final Gemini input = textual + context from graphs
                        prompt_context = summarize_graphs(structured_response.get("graphs", []))
                        final_summary = f"{structured_response['text']}\n\nContext:\n{prompt_context}"

                        deep_prompt = ChatPromptTemplate.from_template(
                            """You are a financial analyst. Based on the summary below, write a deeper analysis, up to 300 words.
                Summarize key insights, trends, anomalies, and possible conclusions for a beginner audience.

                {summary}. at the end, add a disclaimer"""
                        )

                        deep_chain = deep_prompt | get_llm_instance() | StrOutputParser()
                        deep_analysis = deep_chain.invoke({"summary": final_summary})

                    with st.chat_message("assistant"):
                        st.markdown("### 🔍 Deeper Analysis")
                        st.markdown(deep_analysis)
                    st.session_state.chat_history.append({
                    "role": "assistant",
                    "deep_analysis": deep_analysis
                })



                return  # ✅ End here if intent handled

            # SECOND: fallback to Gemini via LangChain
            conversation_history = "\n".join([
                f"User: {m.content}" if isinstance(m, HumanMessage)
                else f"Assistant: {m.content}" if isinstance(m, AIMessage)
                else f"Assistant: {m.get('text', '')}" if isinstance(m, dict) and m.get("role") == "assistant"
                else ""
                for m in get_clean_chat_history()
            ])

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
            
            def get_response(user_query, conversation_history):
                prompt = f"""The following is a conversation between a user and an AI stock assistant. The assistant should remember and refer back to previous facts, including names. Use the context to generate a helpful response.

                {conversation_history}

                User: {user_query}
                Assistant:"""
                prompt = ChatPromptTemplate.from_template(prompt)
                print("prompt:", prompt)
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-lite",
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
            print("stream:",stream)

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

