import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import plotly.express as px

class GraphGenerator:
    def __init__(self):
        # Load Hebrew mapping once
        df = pd.read_excel("company_name_to_ticker.xlsx")
        self.company_name_to_hebrew = {
            row["CompanyName"].strip().upper(): row["HebrewCompanyName"].strip()
            for _, row in df.iterrows()
            if pd.notna(row["CompanyName"]) and pd.notna(row["HebrewCompanyName"])
        }

    def _translate_company_name(self, company_name: str) -> str:
        key = company_name.strip().upper()
        return self.company_name_to_hebrew.get(key, company_name)

    def generate_actual_predicted_forecast_graph(self, df: pd.DataFrame, stock: str, model: str, language: str = "en"):
        labels = {
            "en": {"title": f"Actual, Predicted, and Forecasted Values for {stock} ({model})", "x": "Date", "y": "Value"},
            "he": {"title": f"תחזית מניה עבור {stock} ({model})", "x": "תאריך", "y": "ערך"}
        }

        fig = go.Figure()

        if "Actual" in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Actual"], mode='lines', name='Actual' if language == "en" else "ערך אמיתי", line=dict(color='blue', width=2)))

        if "Predicted" in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Predicted"], mode='lines', name='Predicted' if language == "en" else "חזוי", line=dict(color='orange', width=2, dash='dash')))

        if "Forecasted" in df.columns:
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Forecasted"], mode='lines', name='Forecasted' if language == "en" else "תחזית", line=dict(color='green', width=2, dash='dot')))

        fig.update_layout(
            title=labels[language]["title"],
            xaxis_title=labels[language]["x"],
            yaxis_title=labels[language]["y"],
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_xaxes(tickformat='%Y-%m', tickangle=45, showgrid=True)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_industry_graph(self, df: pd.DataFrame, value_column: str, industry_name: str, language: str = "en"):
        title_map = {
            "en": f"{value_column} Values for {industry_name} Industry",
            "he": f"{value_column} עבור תחום {industry_name}"
        }
        x_label = "Date" if language == "en" else "תאריך"
        y_label = value_column if language == "en" else ("ערך אמיתי" if value_column == "Actual" else "חזוי" if value_column == "Predicted" else "תחזית")

        fig = go.Figure()
        for company, group in df.groupby("Company" if "Company" in df else "Ticker"):
            fig.add_trace(go.Scatter(x=pd.to_datetime(group["Date"], dayfirst=True), y=group[value_column], mode='lines', name=company))

        fig.update_layout(
            title=title_map[language],
            xaxis_title=x_label,
            yaxis_title=y_label,
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickformat='%b %d, %Y', dtick=50 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_comparison_graph(self, dataframes: list, ticker_to_company_name: dict, language: str = "en"):
        fig = go.Figure()
        for ticker, model, df in dataframes:
            name = ticker_to_company_name.get(ticker.replace(".TA", ""), ticker)
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Actual"], mode='lines', name=f"{name} Actual ({model})" if language == "en" else f"{name} ערך אמיתי ({model})", line=dict(dash='solid')))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Predicted"], mode='lines', name=f"{name} Predicted ({model})" if language == "en" else f"{name} חזוי ({model})", line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Forecasted"], mode='lines', name=f"{name} Forecasted ({model})" if language == "en" else f"{name} תחזית ({model})", line=dict(dash='dot')))

        fig.update_layout(
            title="Stock Price Comparison" if language == "en" else "השוואת מחירי מניות",
            xaxis_title="Date" if language == "en" else "תאריך",
            yaxis_title="Price" if language == "en" else "מחיר",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(tickformat='%Y-%m', tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_sector_comparison_graph(self, df: pd.DataFrame, label: str = "Actual", language: str = "en"):
        title = f"Sector Average Comparison – {label}" if language == "en" else f"השוואת מגזרים לפי ממוצע {label}"
        y_label = f"Average {label} Value" if language == "en" else f"ממוצע {label}"
        fig = px.line(
            df,
            x="Date",
            y=label,
            color="Industry",
            title=title,
            labels={label: y_label}
        )
        fig.update_layout(legend_title="Industry" if language == "en" else "תחום", plot_bgcolor="#fdf6e3")
        return fig

    def customize(self, fig):
        fig.update_layout(
            plot_bgcolor="#F9F6E6",
            font=dict(family="Arial, sans-serif", size=15, color="#333333"),
            colorway=["#001219", "#005f73", "#0a9396", "#94d2bd", "#ee9b00", "#ca6702", "#bb3e03", "#9b2226"],
            hoverlabel=dict(font_size=16),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14)),
        )
        return fig

    def synchronize_and_plot_lstm_adjusted_comparison(self, dataframes, company_models: dict, title: str, language: str = "en"):
        all_dates = pd.concat([df["Date"] for _, _, df in dataframes])
        start_date, end_date = all_dates.min(), all_dates.max()

        fig = go.Figure()

        for ticker, model, df in dataframes:
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

            if model in ["LSTM", "GRU"]:
                first_date = df["Date"].iloc[0]
                first_value = df["Actual"].iloc[0]
                backfill_dates = pd.date_range(start=start_date, end=first_date - pd.Timedelta(days=1))

                extended_df = pd.DataFrame({"Date": backfill_dates, "Actual": first_value})
                df = pd.concat([extended_df, df], ignore_index=True)
                df = df[df["Date"] <= end_date]
            else:
                df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

            name = ticker.replace(".TA", "")
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Actual"], mode="lines", name=f"{name} Actual ({model})" if language == "en" else f"{name} ערך אמיתי ({model})", line=dict(dash="solid")))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Predicted"], mode="lines", name=f"{name} Predicted ({model})" if language == "en" else f"{name} חזוי ({model})", line=dict(dash="dash")))

        fig.update_layout(
            title=title if language == "en" else f"השוואה לפי {title}",
            xaxis_title="Date" if language == "en" else "תאריך",
            yaxis_title="Price" if language == "en" else "מחיר",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickformat="%Y-%m", dtick=30 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)

        return self.customize(fig)
