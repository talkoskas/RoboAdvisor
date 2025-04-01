import os
import pandas as pd
from datetime import datetime, timedelta

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, HarmCategory, HarmBlockThreshold


API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCTNncuxKui7XIzrZWt1o_EtLIxiew8qtE")


def get_llm_instance():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
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
            ("system", "You are a helpful AI assistant that talks about Israeli stock market."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_query}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

        self.data_handler = data_handler
        self.graph_generator = graph_generator
        self.intent_detector = intent_detector

    def handle_input(self, user_input: str):
        try:
            intent_data = self.intent_detector.detect(user_input)
            intent = intent_data.get("intent")

            if intent == "industry_values" and "industry" in intent_data:
                return self._handle_industry_intent(intent_data)
            elif intent == "graph" and "company" in intent_data:
                return self._handle_graph_intent(intent_data)
            elif intent == "compare" and "companies" in intent_data and len(intent_data["companies"]) >= 2:
                return self._handle_compare_intent(intent_data)

            return {"text_stream": self._stream_response(user_input)}

        except Exception as e:
            return {"text": f"Oops, something went wrong 😱: {str(e)}"}

    def _stream_response(self, user_query):
        return self.chain.stream({
            "user_query": user_query,
            "chat_history": self.memory.chat_memory.messages
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

