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
from langchain.tools.render import format_tool_to_openai_function

from Levenshtein import distance as levenshtein_distance


API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI")

# Global Configuration
API_KEY = 'AIzaSyC3XqPeca_kNxjsSb64aHvJbJvyakyGKQI'
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"
LSTM_CSV_PATH = "/workspaces/FinalProj/LSTM/actual_vs_pred_lstm_without_reports.csv"
XGBOOST_CSV_PATH = "/workspaces/FinalProj/XGBoost/model_XGBoost_metrics_and_predictions_without_report_parameters.csv"
LIGHTGBM_CSV_PATH = "/workspaces/FinalProj/LightGBM/model_LightGBM_metrics_and_predictions_total.csv"
BEST_MODEL_CSV = "/workspaces/FinalProj/Metrics/without_ARIMA_model_to_stock.csv"
SECTORS_DF_PATH = "sectors_df.csv"
comp_text = pd.read_excel(MAPPING_FILE_PATH).to_markdown(index=False)
sectors_text = pd.read_csv(SECTORS_DF_PATH)[["Industry"]].to_markdown(index=False)

def get_llm_instance(tools=None):
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        stream=True,
        temperature=0.3,
        google_api_key=API_KEY,
        tools=tools,
        enable_automatic_function_calling=True,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
class ChatbotEngine:
    def __init__(self, data_handler, graph_generator, intent_detector):
        self.tools = [
            {
                "name": "graph",
                "description": "Show actual, predicted, and forecasted values for a single company as a graph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_tup": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A tuple (ticker, company name)."
                        }
                    },
                    "required": ["input_tup"]
                }
            },
            {
                "name": "compare",
                "description": "Compare multiple companies’ stock performances.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_tup_lst": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "description": "A list of tuples (ticker, company name)."
                        }
                    },
                    "required": ["input_tup_lst"]
                }
            },
            {
                "name": "industry_values",
                "description": "Return sector-wide stock metrics (actual, predicted, forecasted) for a given sector.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sector_name": {
                            "type": "string",
                            "description": "Exact name of the sector to analyze."
                        }
                    },
                    "required": ["sector_name"]
                }
            },
            {
                "name": "sector_comparison",
                "description": "Compare multiple sectors based on average stock trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sector_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of sector names."
                        }
                    },
                    "required": ["sector_names"]
                }
            }
        ]
        # Register tools

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",  # or "gemini-2.0-flash-lite"
            stream=True,
            temperature=0.3,
            google_api_key=API_KEY,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
            },
            tools=self.tools,           # ✅ here’s the correct fix
            tool_choice="auto"          # ✅ let Gemini pick when to use tools
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        with open("company_name_to_ticker.xlsx", "rb") as f:
            df = pd.read_excel(f)

        valid_names = sorted(set(df["CompanyName"].str.upper().tolist() + df["Ticker"].str.upper().tolist()))
        self.valid_entities_text = "\n".join(f"- {name}" for name in valid_names)



        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             f"You MUST always respond using the function-calling tools if the user's query matches one of the defined tool descriptions.\n\n" 
             f"Never output raw Python code or markdown unless explicitly asked.\n\n" 
             f"Do not answer questions by generating code unless the user says 'give me code' or 'show me how to implement'.\n\n"
            f"You are a chatbot assistant designed to analyze stocks on the Israeli (TA) stock market.\n\n"
            f"🎯 Your primary task is to determine which of the following tools best fits the user's request:\n"
            f"- `'graph'`: Use for a **single company** asking to see actual, predicted, or forecasted values.\n"
            f"- `'compare'`: Use when **two or more companies** are mentioned and the user wants to compare them.\n"
            f"- `'industry_values'`: Use for questions about a **single sector's** overall performance.\n"
            f"- `'sector_comparison'`: Use when comparing **multiple sectors** (e.g., 'tech vs finance').\n\n"
            
            f"🧠 You must reason which tool fits best. If no tool fits well, reply with helpful text.\n"
            f"⚙️ Use function calling whenever a tool clearly matches the prompt.\n"
            f"❌ Do NOT ask for clarification—choose the closest match and proceed.\n\n"

            f"✅ When referencing companies, always use tuples like `('TICKER', 'COMPANY NAME')`.\n"
            f"✅ If the user says 'polim', assume ('POLI','POALIM').\n"
            f"✅ If the user says 'investments', map it to 'Investment & Holdings'.\n\n"

            f"📌 Examples:\n"
            f"- 'Show me teva' → Use `'graph'`\n"
            f"- 'Compare teva and leumi' → Use `'compare'`\n"
            f"- 'How is the banking sector doing?' → Use `'industry_values'`\n"
            f"- 'Compare tech and pharma sectors' → Use `'sector_comparison'`\n\n"

            f"📎 Known companies:\n{self.valid_entities_text}\n\n"
            f"📎 Company Mapping Table:\n{comp_text}\n\n"
            f"📎 Sector Names:\n{sectors_text}\n\n"

            f"⛔ Never hallucinate new tickers or sector names.\n"
            f"If a company/sector isn't recognized, suggest the closest match and ask for confirmation.\n"
            f"Wait for the user to reply 'yes' before proceeding with correction."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_query}")
        ])


        self.chain = self.prompt | self.llm | StrOutputParser()

        self.data_handler = data_handler
        self.graph_generator = graph_generator
        self.intent_detector = intent_detector

    def handle_input(self, user_input: str):
        try:
            # ✅ Retry flow for user accepting a correction
            if user_input.strip().lower() == "yes" and "suggested_correction" in st.session_state:
                corrected_term = st.session_state.pop("suggested_correction")
                last_prompt = st.session_state.get("original_prompt", "")

                ticker_map = self.intent_detector.ticker_mapping
                if corrected_term in ticker_map.values():
                    company_name = [k for k, v in ticker_map.items() if v == corrected_term]
                    if company_name:
                        corrected_term = company_name[0]

                if corrected_term and last_prompt:
                    new_prompt = last_prompt.rsplit(" ", 1)[0] + " " + corrected_term
                    st.session_state.original_prompt = new_prompt
                    st.session_state.chat_history.append(HumanMessage(content=new_prompt))
                    user_input = new_prompt

            # ✅ FIRST: Try IntentDetector logic
            try:
                detected = self.intent_detector.detect(user_input, last_intent=st.session_state.get("last_intent"))
                intent = detected.get("intent")
                st.session_state.last_intent = intent

                if intent == "graph":
                    result = self._handle_graph_intent({"company": detected["company"]})
                    st.session_state["deep_analysis_pending"] = {
                        "summary": result["text"],
                        "context": f"{detected['company']} Stock Forecast"
                    }
                    return result

                elif intent == "compare":
                    result = self._handle_compare_intent({"companies": detected["companies"]})
                    st.session_state["deep_analysis_pending"] = {
                        "summary": result["text"],
                        "context": "Stock Comparison"
                    }
                    return result

                elif intent == "industry_values":
                    result = self._handle_industry_intent({"industry": detected["industry"]})
                    st.session_state["deep_analysis_pending"] = {
                        "summary": result["text"],
                        "context": f"{detected['industry']} Industry"
                    }
                    return result

                elif intent == "sector_comparison":
                    return self._handle_sector_comparison_intent(detected["industries"])  # Already includes deep analysis

            except Exception as e:
                pass  # fallback to Gemini

            # 🤖 Gemini LLM fallback with tool-calling
            response = self.llm.invoke(self.prompt.format_prompt(user_query=user_input).to_messages())

            st.session_state.chat_history.append(HumanMessage(content=user_input))
            st.session_state.chat_history.append(AIMessage(content=response.content))

            if response.tool_calls:
                return self._handle_tool_call(response)

            return {"text": response.content, "intent": "fallback", "raw_input": user_input}

        except Exception as e:
            print(e)
            user_words = user_input.upper().split()
            all_companies = list(self.intent_detector.ticker_mapping.keys())
            all_tickers = list(self.intent_detector.ticker_mapping.values())
            all_industries = list(self.intent_detector.industry_mapping.values())

            matched_companies = [w for w in user_words if w in all_companies]
            matched_tickers = [w for w in user_words if w in all_tickers]
            matched_industries = [w for w in user_words if w in all_industries]

            if len(matched_companies) + len(matched_tickers) == 1:
                company = matched_companies[0] if matched_companies else next(
                    (k for k, v in self.intent_detector.ticker_mapping.items() if v in matched_tickers), None
                )
                if company:
                    return self._handle_graph_intent({"company": company})

            if len(matched_industries) == 1:
                return self._handle_industry_intent({"industry": matched_industries[0]})

            last_word = user_words[-1]
            all_names = all_companies + all_tickers + all_industries
            best_match = min(all_names, key=lambda x: levenshtein_distance(x, last_word))
            if levenshtein_distance(best_match, last_word) <= 2:
                st.session_state.suggested_correction = best_match
                st.session_state.original_prompt = user_input
                return {
                    "text": f"⚠️ I couldn’t recognize '{last_word}'. Did you mean **{best_match}**?\n\nIf yes, reply with 'yes' to continue."
                }

            return {
                "text": f"❌ Sorry, I couldn't recognize '{last_word}' and no close match was found.\n\n{str(e)}",
                "intent": "fallback"
            }


    def _stream_response(self, user_query):
        def convert_valid_message(m):
            if isinstance(m, (HumanMessage, AIMessage)):
                return m
            elif isinstance(m, dict):
                role = m.get("role")
                if role == "user" and "text" in m:
                    return HumanMessage(content=m["text"])
                elif role == "assistant" and "text" in m:
                    return AIMessage(content=m["text"])
                elif role == "assistant" and "deep_analysis" in m:
                    return AIMessage(content=m["deep_analysis"])
            return None

        cleaned_history = [
            convert_valid_message(m)
            for m in st.session_state.chat_history
        ]
        cleaned_history = [m for m in cleaned_history if m is not None]

        return self.chain.stream({
            "user_query": user_query,
            "chat_history": cleaned_history  # Now safe for MessagesPlaceholder
        })




    def _record_response(self, user_input, response):
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(response)

    # ====== Intent Handlers (static text, no stream) ======

    def _handle_industry_intent(self, intent_data):
        industry = intent_data["industry"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

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
        end_date = datetime(2024, 12, 31)

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
        end_date = datetime(2024, 12, 31)
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
