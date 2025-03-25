import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

class GraphGenerator:
    def __init__(self):
        pass

    def generate_actual_predicted_forecast_graph(self, df: pd.DataFrame, stock: str, model: str):
        """
        Generates a full line chart for Actual, Predicted, and Forecasted data.
        """
        fig = go.Figure()

        if "Actual" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode='lines', name='Actual',
                line=dict(color='blue', width=2)
            ))

        if "Predicted" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode='lines', name='Predicted',
                line=dict(color='orange', width=2, dash='dash')
            ))

        if "Forecasted" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Forecasted"],
                mode='lines', name='Forecasted',
                line=dict(color='green', width=2, dash='dot')
            ))

        fig.update_layout(
            title=f"Actual, Predicted, and Forecasted Values for {stock} ({model})",
            xaxis_title="Date",
            yaxis_title="Value",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_xaxes(tickformat='%Y-%m', tickangle=45, showgrid=True)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_sector_graph(self, df: pd.DataFrame, value_column: str, sector_name: str):
        """
        Plots all companies in a sector using the specified column (Actual or Predicted).
        """
        fig = go.Figure()
        for company, group in df.groupby("Company" if "Company" in df else "Ticker"):
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(group["Date"], dayfirst=True),
                y=group[value_column],
                mode='lines',
                name=company
            ))

        fig.update_layout(
            title=f"{value_column} Values for {sector_name} Sector",
            xaxis_title="Date",
            yaxis_title=value_column,
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_xaxes(tickformat='%b %d, %Y', dtick=50 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def generate_comparison_graph(self, dataframes: list, ticker_to_company_name: dict):
        """
        Plots multiple companies with actual, predicted, and forecasted lines.
        `dataframes`: list of (ticker, model, combined_df)
        """
        fig = go.Figure()
        for ticker, model, df in dataframes:
            name = ticker_to_company_name.get(ticker.replace(".TA", ""), ticker)

            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode='lines',
                name=f"{name} Actual ({model})",
                line=dict(dash='solid')
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode='lines',
                name=f"{name} Predicted ({model})",
                line=dict(dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Forecasted"],
                mode='lines',
                name=f"{name} Forecasted ({model})",
                line=dict(dash='dot')
            ))

        fig.update_layout(
            title="Stock Price Comparison",
            xaxis_title="Date",
            yaxis_title="Price",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_xaxes(tickformat='%Y-%m', tickangle=45)
        fig.update_yaxes(showgrid=True)
        return self.customize(fig)

    def customize(self, fig):
        """
        Applies a consistent theme to the plot.
        """
        fig.update_layout(
            plot_bgcolor="#F9F6E6",
            font=dict(family="Arial, sans-serif", size=15, color="#333333"),
            colorway=["#001219", "#005f73", "#0a9396", "#94d2bd", "#ee9b00", "#ca6702", "#bb3e03", "#9b2226"],
            hoverlabel=dict(font_size=16),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14)),
        )
        return fig

    def synchronize_and_plot_lstm_adjusted_comparison(self, dataframes, company_models: dict, title: str):
        """
        Synchronize time ranges across models (handling LSTM/GRU specially),
        then plot a comparative graph.
        """
        # Determine full date range
        all_dates = pd.concat([df["Date"] for _, _, df in dataframes])
        start_date, end_date = all_dates.min(), all_dates.max()

        fig = go.Figure()

        for ticker, model, df in dataframes:
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

            if model in ["LSTM", "GRU"]:
                # Extend backwards with first Actual value
                first_date = df["Date"].iloc[0]
                first_value = df["Actual"].iloc[0]
                backfill_dates = pd.date_range(start=start_date, end=first_date - pd.Timedelta(days=1))

                extended_df = pd.DataFrame({"Date": backfill_dates, "Actual": first_value})
                df = pd.concat([extended_df, df], ignore_index=True)

                # Cut off future dates
                df = df[df["Date"] <= end_date]
            else:
                # Truncate to range
                df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

            name = ticker.replace(".TA", "")
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Actual"],
                mode="lines", name=f"{name} Actual ({model})",
                line=dict(dash="solid")
            ))
            fig.add_trace(go.Scatter(
                x=df["Date"], y=df["Predicted"],
                mode="lines", name=f"{name} Predicted ({model})",
                line=dict(dash="dash")
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Price",
            height=600,
            width=1000,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(tickformat="%Y-%m", dtick=30 * 24 * 60 * 60 * 1000, tickangle=45)
        fig.update_yaxes(showgrid=True)

        return self.customize(fig)
