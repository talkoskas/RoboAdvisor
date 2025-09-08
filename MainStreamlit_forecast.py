# MainStreamlit_forecast.py
import streamlit as st
from pathlib import Path
import sys

# ── Path setup so fullstack imports work both locally and on Streamlit Cloud ──
BASE_DIR = Path(__file__).resolve().parent
FULLSTACK_DIR = BASE_DIR / "fullstack"
if str(FULLSTACK_DIR) not in sys.path:
    sys.path.insert(0, str(FULLSTACK_DIR))

import os
import pandas as pd
import uuid
import warnings
from plotly.io import from_json, to_json

# Core / app components
from chatbot_engine import ChatbotEngine
from langchain_core.messages import AIMessage, HumanMessage
from intent_detector import IntentDetector
from stock_data_handler import StockDataHandler
from graph_generator import GraphGenerator

# DB utilities
from fullstack.database_mongo import (
    get_chat_by_id, get_chats_by_user, create_chat, update_chat, delete_chat
)

warnings.filterwarnings("ignore")

# ── Global Configuration ──────────────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_DEV_KEY_HERE")
LSTM_CSV_PATH    = os.path.join("LSTM", "actual_vs_pred_lstm_without_reports.csv")
XGBOOST_CSV_PATH = os.path.join("XGBoost", "model_XGBoost_metrics_and_predictions_without_report_parameters.csv")
LIGHTGBM_CSV_PATH = os.path.join("LightGBM", "model_LightGBM_metrics_and_predictions_total.csv")
BEST_MODEL_CSV   = os.path.join("Metrics", "without_ARIMA_model_to_stock.csv")
SECTORS_DF_PATH  = "sectors_df.csv"
MAPPING_FILE_PATH = "company_name_to_ticker.xlsx"

# ── Session defaults ──────────────────────────────────────────────────────────
if "mentioned_tickers" not in st.session_state:
    st.session_state.mentioned_tickers = set()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- module-level: safe chat hydration helper (no rerun) ---
def load_chat_into_state(chat_doc: dict):
    """
    Hydrate st.session_state.chat_history from a chat document (dict with 'chat_history' list).
    Does NOT rerun. Shows both user turns and assistant turns (incl. graphs and deep_analysis).
    """
    from langchain_core.messages import HumanMessage  # ensure import
    st.session_state.chat_history = []

    def _extract_text(m: dict) -> str:
        for k in ("content", "text", "message", "summary"):
            v = m.get(k)
            if isinstance(v, str) and v.strip():
                return v
        for _, v in m.items():
            if isinstance(v, str) and v.strip():
                return v
        return ""

    def _extract_graphs(m: dict):
        out = []
        raw = m.get("graphs") or m.get("figures") or []
        for item in raw:
            try:
                fig = from_json(item) if isinstance(item, (str, dict)) else None
                if fig is not None:
                    out.append(fig)
            except Exception:
                pass
        return out

    for m in (chat_doc or {}).get("chat_history", []):
        role   = m.get("role")
        text   = _extract_text(m)
        graphs = _extract_graphs(m)
        deep   = m.get("deep_analysis")

        if not (text.strip() or graphs or deep):
            continue

        if role == "user":
            st.session_state.chat_history.append(HumanMessage(content=text))
        else:
            row = {"role": "assistant", "content": text, "graphs": graphs}
            if deep:
                row["deep_analysis"] = deep
            st.session_state.chat_history.append(row)

# ── Utility: serialize chat history for MongoDB ───────────────────────────────
def _serialize_history_for_db(history: list) -> list[dict]:
    """Convert session_state.chat_history into a Mongo-friendly list of dicts."""
    out = []
    for m in history:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        elif isinstance(m, dict) and m.get("role") == "assistant":
            graphs = []
            for fig in m.get("graphs", []) or []:
                try:
                    graphs.append(to_json(fig))
                except Exception:
                    pass
            entry = {
                "role": "assistant",
                "content": m.get("content", "") or m.get("text", "") or "",
            }
            if graphs:
                entry["graphs"] = graphs
            if m.get("deep_analysis"):
                entry["deep_analysis"] = m["deep_analysis"]
            out.append(entry)
        elif isinstance(m, AIMessage):
            out.append({"role": "assistant", "content": m.content})
    return out

# ── Main App Controller ───────────────────────────────────────────────────────
class AppManager:
    """
    Manages the full Streamlit application lifecycle for the Robo Advisor chatbot.
    - Handles onboarding/disclaimer
    - Chat session management (list, switch, new, delete)
    - Renders bot conversation + figures
    - Triggers deeper analysis prompts per-chat without duplication
    """

    def __init__(self):
        # Core components
        self.api_key = API_KEY
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

    # ── Data loaders ───────────────────────────────────────────────────────────
    def load_ticker_mapping(self) -> dict:
        df = pd.read_excel(MAPPING_FILE_PATH)
        return {row["CompanyName"].upper(): row["Ticker"].upper() for _, row in df.iterrows()}

    def load_industry_mapping(self) -> dict:
        df = pd.read_csv(SECTORS_DF_PATH).dropna(subset=["Industry"])
        canonical = df["Industry"].unique()
        mapping = {}
        for industry in canonical:
            cleaned = (
                str(industry).lower()
                .replace("-", " ").replace(":", " ")
                .replace("_", " ").replace(",", " ")
            )
            cleaned = " ".join(cleaned.split())
            mapping[cleaned] = industry.strip()
        return mapping

    # ── Main UI ───────────────────────────────────────────────────────────────
    def run(self):
        # ── Authentication guard: must be logged in before anything else ──────
        if not st.session_state.get("authenticated"):
            from fullstack import login_ui
            login_ui.display_login()
            return

        # Container for per-chat pending prompts
        if "pending_by_chat" not in st.session_state:
            st.session_state.pending_by_chat = {}

        # Nonce used to force re-instantiation of chat selectbox after create/delete
        if "chat_widget_nonce" not in st.session_state:
            st.session_state.chat_widget_nonce = 0

        # ── Helpers ───────────────────────────────────────────────────────────
        def _reload_chats(username: str):
            chats = sorted(
                get_chats_by_user(username),
                key=lambda m: m["last_updated"],
                reverse=True
            )
            st.session_state["available_chats"] = chats
            return chats

        def _has_blank_chat(username: str) -> bool:
            """True if a chat exists with no user messages."""
            for meta in get_chats_by_user(username):
                doc = get_chat_by_id(meta["_id"]) or {}
                hist = doc.get("chat_history", []) or []
                has_user = any((m.get("role") == "user" and (m.get("content") or "").strip()) for m in hist)
                if not has_user:
                    return True
            return False

        # ── Onboarding / Disclaimer (only after login) ────────────────────────
        if "accepted_disclaimer" not in st.session_state:
            st.session_state.accepted_disclaimer = False

        if not st.session_state.accepted_disclaimer:
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
""")

            st.markdown("## ⚙️ How Does It Work?")
            st.markdown("""
- **LSTM / GRU** → sequence-aware models for time-series forecasting  
- **XGBoost / LightGBM** → powerful tree-based models for structured tabular data  
""")

            st.markdown("## 🎓 Academic Context")
            st.markdown("""
This application was developed as part of a **Fintech Project** at **The Academic College of Tel-Aviv Yaffo (MTA)**, by students in the Department of Computer Science.
""")

            st.markdown("## ⚠️ Disclaimer")
            st.warning("""
The chatbot's responses are **not binding financial recommendations** and do **not replace professional advice**.  
All outputs are based on historical data and model estimations and are provided for educational purposes only.
""")

            if st.button("✅ I understand and wish to continue"):
                st.session_state.accepted_disclaimer = True
                st.rerun()
            return

        # ── Main page title / greeting ────────────────────────────────────────
        user = st.session_state.get("username", None)
        if user:
            st.markdown(f"### Hello, **{user}** 👋")
        st.title("🤖 Robo Advisor – Israeli Stock Market")

        # # --- Debug: Live overlay ---
        # st.sidebar.checkbox("🔧 Debug live overlay", key="debug_live_overlay", value=True)
        # if st.session_state.get("debug_live_overlay"):
        #     with st.sidebar.expander("Live overlay debug", expanded=False):
        #         st.write("last_live_error:", st.session_state.get("last_live_error"))
        #         st.write("live_overlay_attempts:", st.session_state.get("live_overlay_attempts"))
        #         st.write("live_overlay_rows:", st.session_state.get("live_overlay_rows"))
        #         st.write("last_live_ticker:", st.session_state.get("last_live_ticker"))
        #         st.write("last_actual_date:", st.session_state.get("last_actual_date"))

        # ── SIDEBAR: Chats / New / Delete / Logout ────────────────────────────
        st.sidebar.title("About")
        st.sidebar.info("This chatbot provides stock analysis using historical and forecasted data.")
        st.sidebar.title("Your Chats")
        username = st.session_state.get("username")

        # Initial load or explicit refresh
        if "available_chats" not in st.session_state or st.session_state.get("_refresh_chats"):
            _reload_chats(username)
            st.session_state["_refresh_chats"] = False

        chats = st.session_state.get("available_chats", [])

        # Human-readable labels from the first user message; fallback to "New Chat"
        labels_by_id = {}
        ids = []
        for meta in chats:
            cid = str(meta["_id"])
            ids.append(cid)
            doc = get_chat_by_id(meta["_id"]) or {}
            first_user_text = next(
                (m.get("content", "").strip()
                 for m in doc.get("chat_history", [])
                 if m.get("role") == "user" and m.get("content")), ""
            )
            labels_by_id[cid] = first_user_text or "New Chat"

        # Ensure we have a current selection
        if ids and ("current_chat_id" not in st.session_state or st.session_state["current_chat_id"] not in ids):
            st.session_state["current_chat_id"] = ids[0]

        # Dynamic key for selectbox to allow re-instantiation after create/delete
        widget_key = f"selected_chat_id_{st.session_state.chat_widget_nonce}"
        default_idx = 0
        if st.session_state.get("current_chat_id") in ids:
            default_idx = ids.index(st.session_state["current_chat_id"])

        # Callback to hydrate immediately on selection change (no rerun needed)
        def _on_chat_select_change():
            selected_id_now = st.session_state.get(widget_key)
            if not selected_id_now:
                return
            if selected_id_now != st.session_state.get("current_chat_id"):
                st.session_state["current_chat_id"] = selected_id_now
                doc = get_chat_by_id(selected_id_now) or {}
                load_chat_into_state(doc)
                # Clear any pending deeper-analysis for the newly active chat
                if "pending_by_chat" in st.session_state:
                    st.session_state["pending_by_chat"].pop(selected_id_now, None)
                st.session_state["_hydrated_chat_id"] = selected_id_now

        if ids:
            st.sidebar.selectbox(
                "Switch chats",
                options=ids,
                index=default_idx,
                format_func=lambda cid: labels_by_id.get(cid, cid),
                key=widget_key,
                on_change=_on_chat_select_change,
            )

            # Ensure hydration for initial load (first render or after rerun)
            active_id = st.session_state.get("current_chat_id")
            if active_id and st.session_state.get("_hydrated_chat_id") != active_id:
                doc = get_chat_by_id(active_id) or {}
                load_chat_into_state(doc)
                st.session_state["_hydrated_chat_id"] = active_id
        else:
            st.sidebar.info("No chats yet. Start a new conversation to see it here.")

        # ➕ New Chat (only if there’s no existing blank chat)
        if st.sidebar.button("➕ New chat", use_container_width=True):
            if _has_blank_chat(username):
                st.sidebar.info("You already have an empty chat. Use it or start talking there.")
            else:
                new_id = create_chat(username, [], None)
                st.session_state["current_chat_id"] = str(new_id)
                st.session_state["_refresh_chats"] = True
                st.session_state.pop("_hydrated_chat_id", None)
                st.session_state["chat_history"] = []
                # Force selectbox to be recreated with new default selection
                st.session_state.chat_widget_nonce += 1
                st.rerun()

        # 🗑️ Delete current chat
        if ids:
            with st.sidebar.expander("Danger zone", expanded=False):
                if st.button("🗑️ Delete current chat", type="primary", use_container_width=True):
                    curr_id = st.session_state.get("current_chat_id")
                    if curr_id and delete_chat(curr_id, username):
                        st.success("Chat deleted.")
                        st.session_state["_refresh_chats"] = True
                        st.session_state.pop("_hydrated_chat_id", None)
                        st.session_state["chat_history"] = []

                        remaining = sorted(get_chats_by_user(username), key=lambda m: m["last_updated"], reverse=True)
                        if remaining:
                            st.session_state["current_chat_id"] = str(remaining[0]["_id"])
                        else:
                            st.session_state["current_chat_id"] = None

                        # Recreate the selectbox cleanly
                        st.session_state.chat_widget_nonce += 1
                        st.rerun()
                    else:
                        st.error("Failed to delete chat. Please try again.")

        # 🚪 Logout
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            try:
                import extra_streamlit_components as stx
                cm = stx.CookieManager()
                if cm.get("auth_token"):
                    cm.delete("auth_token")
            except Exception:
                pass
            st.session_state.clear()
            st.rerun()

        # ── Chat UI (center pane) ─────────────────────────────────────────────
        default_prompts = [
            "show me the graph of leumi",
            "compare leumi and poalim",
            "show me all banks"
        ]
        cols = st.columns(len(default_prompts))
        selected_prompt = None
        for i, p in enumerate(default_prompts):
            if cols[i].button(p, use_container_width=True):
                selected_prompt = p

        # Re-render history
        for msg_idx, message in enumerate(st.session_state.get("chat_history", [])):
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.write(message.content)
            elif isinstance(message, dict) and message.get("role") == "assistant":
                with st.chat_message("assistant"):
                    for fig_idx, fig in enumerate(message.get("graphs", [])):
                        st.plotly_chart(fig, use_container_width=True, key=f"chat{msg_idx}_fig{fig_idx}")
                    content = message.get("content")
                    if content:
                        lang = st.session_state.get("language", "en")
                        align = "right" if lang == "he" else "left"
                        dir_ = "rtl" if lang == "he" else "ltr"
                        st.markdown(
                            f'<div dir="{dir_}" style="text-align: {align}; font-size: 18px;">{content}</div>',
                            unsafe_allow_html=True
                        )
                    deep = message.get("deep_analysis")
                    if deep:
                        st.markdown("### 🔍 Deeper Analysis")
                        lang = st.session_state.get("language", "en")
                        align = "right" if lang == "he" else "left"
                        dir_ = "rtl" if lang == "he" else "ltr"
                        st.markdown(
                            f'<div dir="{dir_}" style="text-align: {align}; font-size: 18px;">{deep}</div>',
                            unsafe_allow_html=True
                        )
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(message.content)

        # Input
        manual_input = st.chat_input("What would you like to know?")
        prompt = selected_prompt or manual_input

        if prompt:
            st.session_state["language"] = "he" if any('\u0590' <= c <= '\u05EA' for c in prompt) else "en"
            user_msg = HumanMessage(content=prompt)
            st.session_state.chat_history.append(user_msg)
            with st.chat_message("user"):
                st.write(prompt)

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

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": structured_response.get("text", ""),
                "graphs": structured_response.get("graphs", [])
            })

            # Persist chat after each exchange
            cid = st.session_state.get("current_chat_id")
            if cid:
                try:
                    payload = _serialize_history_for_db(st.session_state.chat_history)
                    update_chat(cid, payload)
                except Exception as e:
                    st.warning(f"Could not save chat: {e}")

            # ── Set (only) the pending deeper-analysis prompt for this active chat
            active_id = st.session_state.get("current_chat_id")
            intent_raw = (structured_response.get("intent") or "").strip().lower()
            graphs_exist = bool(structured_response.get("graphs"))
            intent_whitelist = {
                "graph", "graphs", "compare", "comparison",
                "industry", "industry_values",
                "sector", "sector_comparison",
                "addition", "forecast", "analysis", "visualize"
            }
            should_offer_deep = graphs_exist or (intent_raw in intent_whitelist)

            if should_offer_deep and active_id:
                st.session_state.pending_by_chat[active_id] = {
                    "summary": structured_response.get("text", "") or "",
                    "context": f"{(intent_raw or 'analysis').capitalize()}",
                }

        # ── Single global renderer for deeper-analysis prompt (no duplicates) ──
        active_id = st.session_state.get("current_chat_id")
        pending = st.session_state.pending_by_chat.get(active_id) if active_id else None

        if pending:
            st.markdown("### 🔍 Would you like a deeper analysis?")
            c1, c2 = st.columns([1, 1])

            yes_clicked = c1.button("🎨 Yes, show me!", use_container_width=True, key=f"deep_yes_{active_id}")
            no_clicked = c2.button("❌ No thanks", use_container_width=True, key=f"deep_no_{active_id}")

            if yes_clicked:
                # Consume pending BEFORE generating, so we don't re-render the prompt this run.
                st.session_state.pending_by_chat.pop(active_id, None)
                with st.spinner("🔍 Generating deeper analysis..."):
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
                cid = st.session_state.get("current_chat_id")
                if cid:
                    try:
                        payload = _serialize_history_for_db(st.session_state.chat_history)
                        update_chat(cid, payload)
                    except Exception as e:
                        st.warning(f"Could not save chat: {e}")

            elif no_clicked:
                # Clear and *immediately* rerun so the prompt disappears on the first click.
                st.session_state.pending_by_chat.pop(active_id, None)
                st.rerun()


# ── Entrypoint: respect fullstack.app routing if present ─────────────────────
if __name__ == "__main__":
    # The fullstack.app module owns the top-level routing between
    # login / registration / reset / main app.
    from fullstack.app import display_main_app, display_login, display_registration, display_password_reset

    if st.session_state.get("authenticated"):
        display_main_app()
    elif st.session_state.get("reset_password"):
        display_password_reset()
    elif st.session_state.get("registration"):
        display_registration()
    else:
        display_login()
