import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold


API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI")

# Global Configuration
API_KEY = 'AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI'
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"
LSTM_CSV_PATH = "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm.csv"
XGBOOST_CSV_PATH = "/workspaces/FinalProj/XGBoost/model_XGBoost_metrics_and_predictions.csv"
LIGHTGBM_CSV_PATH = "/workspaces/FinalProj/LightGBM/LightGBM_metrics_and_predictions.csv"
BEST_MODEL_CSV = "/workspaces/FinalProj/Metrics/without_ARIMA_model_to_stock.csv"
SECTORS_DF_PATH = "sectors_df.csv"
comp_text = pd.read_excel(MAPPING_FILE_PATH).to_markdown(index=False)
sectors_text = pd.read_csv(SECTORS_DF_PATH)[["Market Sector"]].to_markdown(index=False)
def get_llm_instance():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        stream=True,
        temperature=0.3,
        google_api_key=API_KEY,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )


class ChatbotEngine:
    def __init__(self, data_handler, graph_generator, intent_detector):
        self.llm = get_llm_instance()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "you are a chat bot designed to help with stock analysis and "
                   "recommendations over the Israeli (TA) stock market."
                   " You will do function calling and textual answers."
                   " When you return a graph, add analysis and recommendations. "
                   "Please be nice and polite."
                   "When youre needed to reference one or more companies, use tuple (ticker, company name)."
                   "the tickers from the provided mapping file:"
                    f"{comp_text}"
                    "Alternatively, you might need to select sector names, use only from: "
                    f"{sectors_text}"
                    "for both files, use the exact name as shown in the table."
                    "for example, if asked about company 'teba', assume user asked about TEVA "
                   "and use the tuple ('TEVA','TEVA') in this order."
                    "if asked about sector investments, use Investment & Holdings sector."
                   "When asked about multiple companies, return a list of tuples."
                   "like, if asked about 'poli' and 'teva', return [('POLI','POALIM'),('TEVA','TEVA')]."
                   "use function calling if needed."
                   "If the user asks to 'add' a stock to a previous comparison, call the 'compare' function again with"
                   " all the stocks, including the new one. For example, if the user asks 'compare teva and leumi' "
                   "and then 'add afcon', call compare with [('TEVA','TEVA'),('LUMI','LEUMI'),('AFCO','AFCON')]."
                   "The 'compare' function is only for comparing specific stocks, not sectors."
                   "look for continuation requests in general."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_query}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

        self.data_handler = data_handler
        self.graph_generator = graph_generator
        self.intent_detector = intent_detector

    def handle_input(self, user_input: str):
        try:
            last_intent = st.session_state.get("last_intent")
            intent_data = self.intent_detector.detect(user_input, last_intent=last_intent)

            intent = intent_data.get("intent")
            st.session_state.last_intent = intent
            # 🔁 If user said "add <company>" or "compare with <company>", build compare list
            if intent == "compare" and "add_company" in intent_data:
                previous = st.session_state.get("last_companies") or []

                # If only 1 previous stock (from 'graph'), promote it to compare list
                if not previous and st.session_state.get("last_company"):
                    previous = [st.session_state["last_company"]]

                combined = list(set(previous + [intent_data["add_company"]]))
                response = self._handle_compare_intent({"companies": combined})

                # Update session state
                st.session_state.last_companies = combined
                st.session_state.last_intent = "compare"

                return {**response, "intent": "compare", "raw_input": user_input}

            if intent == "sector_comparison" and "add_industry" in intent_data:
                previous = st.session_state.get("last_industry")

                if not previous:
                    return {"text": "Oops, I couldn't find a previous industry to compare with."}

                industries = [previous, intent_data["add_industry"]]
                response = self._handle_sector_comparison_intent(industries)

                st.session_state.last_intent = "sector_comparison"
                st.session_state.last_industries = industries
                return {**response, "intent": "sector_comparison", "raw_input": user_input}

            if intent == "industry_values" and "industry" in intent_data:
                response = self._handle_industry_intent(intent_data)
                st.session_state.last_industry = intent_data.get("industry")
            elif intent == "graph" and "company" in intent_data:
                response = self._handle_graph_intent(intent_data)
                st.session_state.last_company = intent_data.get("company")
            elif intent == "compare" and "companies" in intent_data and len(intent_data["companies"]) >= 2:
                response = self._handle_compare_intent(intent_data)
                st.session_state.last_companies = intent_data.get("companies")
            else:
                response_chunks = self._stream_response(user_input)
                return {"text": "".join(response_chunks), "intent": "fallback"}

            response["intent"] = intent  # ✅ attach intent to return value
            response["raw_input"] = user_input
            return response


        except Exception as e:
            return {"text": f"Oops, something went wrong 😱: {str(e)}"}

    def _stream_response(self, user_query):
            def convert_message(msg):
                if isinstance(msg, HumanMessage):
                    return {"role": "user", "content": msg.content}
                elif isinstance(msg, AIMessage):
                    return {"role": "assistant", "content": msg.content}
                elif isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        return msg  # already good
                    elif "role" in msg and "text" in msg:
                        return {"role": msg["role"], "content": msg["text"]}
                    elif "role" in msg and "deep_analysis" in msg:
                        return {"role": msg["role"], "content": msg["deep_analysis"]}
                return None

            formatted_history = [convert_message(m) for m in st.session_state.chat_history]
            formatted_history = [m for m in formatted_history if m is not None]

            return self.chain.stream({
                "user_query": user_query,
                "chat_history": formatted_history
            })


    def _record_response(self, user_input, response):
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(response)

    # ====== Intent Handlers (static text, no stream) ======

    def _handle_industry_intent(self, intent_data):
        industry = intent_data["industry"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 3, 13)

        actual_df = self.data_handler.get_industry_actuals(industry, start_date, end_date)
        predicted_df = self.data_handler.get_industry_predictions(industry, start_date, end_date)
        best_model_df = pd.read_csv(self.data_handler.best_model_path)

        forecast_dfs = []
        ticker_to_company = {v: k for k, v in self.data_handler.ticker_mapping.items()}

        for ticker in actual_df["Ticker"].dropna().unique():
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

        fig_actual = self.graph_generator.generate_industry_graph(actual_df, "Actual", industry)
        fig_pred = self.graph_generator.generate_industry_graph(predicted_df, "Predicted", industry)
        fig_forecast = self.graph_generator.generate_industry_graph(full_forecast_df, "Forecasted", industry)

        summary = self._generate_industry_summary(actual_df, predicted_df, full_forecast_df, ticker_to_company, industry)
        st.session_state.last_industry = industry

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
        text = self._generate_single_stock_summary(company, data, forecast, model)
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
                summaries.append(self._generate_single_stock_summary(
                    ticker_to_company.get(ticker.replace(".TA", ""), ticker), data, forecast, model))
            except:
                continue

        if not combined_dataframes:
            return {"text": "No valid data found for comparison."}

        fig = self.graph_generator.generate_comparison_graph(combined_dataframes, ticker_to_company)
        summary = self._generate_comparison_summary(summaries)
        return {"text": summary, "graphs": [fig]}
    def _handle_sector_comparison_intent(self, industries):
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 3, 13)

        industry_avg_frames = []
        summaries = []

        for industry in industries:
            actual_df = self.data_handler.get_industry_actuals(industry, start_date, end_date)
            if actual_df.empty:
                continue

            avg_df = actual_df.groupby("Date")["Actual"].mean().reset_index()
            avg_df["Industry"] = industry
            industry_avg_frames.append(avg_df)

            # Basic summary per sector
            first = avg_df["Actual"].iloc[0]
            last = avg_df["Actual"].iloc[-1]
            trend = "upward 📈" if last > first else "downward 📉"
            summaries.append(f"- {industry}: Start={first:.2f}, End={last:.2f}, Trend={trend}")

        if not industry_avg_frames:
            return {"text": "No data found for the selected industries."}

        combined_df = pd.concat(industry_avg_frames)
        fig = self.graph_generator.generate_sector_comparison_graph(combined_df)

        summary_text = f"📊 Sector comparison between industries:\n\n" + "\n".join(summaries)

        # 🔍 Generate deeper analysis using Gemini
        deep_analysis = self._generate_deeper_analysis(summary_text, context_info="Sector Comparison")

        return {
            "text": summary_text + "\n\n🔍 **Deeper Analysis**\n\n" + deep_analysis,
            "graphs": [fig]
        }



    def _generate_industry_summary(self, actual_df, predicted_df, forecast_df, name_map, industry):
        def summarize(df, col):
            summary = []
            for ticker in df["Ticker"].unique():
                sub = df[df["Ticker"] == ticker]
                company = name_map.get(ticker.replace(".TA", ""), ticker)
                min_, max_, mean_ = sub[col].min(), sub[col].max(), sub[col].mean()
                trend = "upward" if sub[col].iloc[-1] > sub[col].iloc[0] else "downward"
                summary.append(f"- {company}: Min={min_:.2f}, Max={max_:.2f}, Mean={mean_:.2f}, Trend={trend}")
            return "\n".join(summary)

        return (
            f"📊 industry-wide summary for {industry} industry:\n\n"
            f"**Actuals:**\n{summarize(actual_df, 'Actual')}\n\n"
            f"**Predictions:**\n{summarize(predicted_df, 'Predicted')}\n\n"
            f"**Forecasts:**\n{summarize(forecast_df, 'Forecasted')}"
        )

    def _generate_single_stock_summary(self, company, data, forecast_df, model):
        def stats(col):
            return {
                "min": data[col].min(),
                "max": data[col].max(),
                "mean": data[col].mean(),
                "trend": "upward" if data[col].iloc[-1] > data[col].iloc[0] else "downward"
            }

        actual = stats("Actual")
        predicted = stats("Predicted")
        forecast = {
            "min": forecast_df["Forecasted"].min(),
            "max": forecast_df["Forecasted"].max(),
            "mean": forecast_df["Forecasted"].mean(),
            "trend": "upward" if forecast_df["Forecasted"].iloc[-1] > forecast_df["Forecasted"].iloc[0] else "downward"
        }

        return (
            f"📈 Stock analysis for {company} using model: **{model}**\n"
            f"- Actual: Min={actual['min']:.2f}, Max={actual['max']:.2f}, Mean={actual['mean']:.2f}, Trend={actual['trend']}\n"
            f"- Predicted: Min={predicted['min']:.2f}, Max={predicted['max']:.2f}, Mean={predicted['mean']:.2f}, Trend={predicted['trend']}\n"
            f"- Forecasted: Min={forecast['min']:.2f}, Max={forecast['max']:.2f}, Mean={forecast['mean']:.2f}, Trend={forecast['trend']}"
        )

    def _generate_comparison_summary(self, summaries):
        return "📊 Comparison Summary:\n\n" + "\n\n".join(summaries)
    def _generate_deeper_analysis(self, summary: str, context_info: str = "") -> str:
        """
        Uses Gemini to generate deeper analysis from an existing summary and optional metadata.
        """
        prompt_text = (
            "You are a financial analyst. Based on the given summary, values, and context, "
            "write a **deeper analysis** including patterns, anomalies, risks, and insights. "
            "Explain trends and make it educational for a beginner-level audience.\n\n"
            f"Context:\n{context_info}\n\nSummary:\n{summary}"
        )

        llm = get_llm_instance()
        chain = ChatPromptTemplate.from_template("{prompt}") | llm | StrOutputParser()
        result = chain.invoke({"prompt": prompt_text})
        return result


