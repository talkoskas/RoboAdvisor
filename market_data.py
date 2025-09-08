# market_data.py
from __future__ import annotations
import os
import pandas as pd
import datetime as dt

try:
    import yfinance as yf
except ImportError:
    raise ImportError("Please install yfinance: pip install yfinance")

CACHE_DIR = os.path.join(".cache_prices")
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(ticker: str) -> str:
    return os.path.join(CACHE_DIR, f"{ticker.upper()}.parquet")

def get_price_history(
    tickers: list[str] | tuple[str, ...],
    start: str | dt.date | None = None,
    end: str | dt.date | None = None,
    interval: str = "1d",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Returns a DataFrame with a multi-column layout:
    - index = DatetimeIndex
    - columns = (ticker, field) like ('AAPL', 'Close'), ('AAPL','Open'), etc.
    Uses local parquet cache per ticker and incrementally fetches only missing days.
    """
    if isinstance(tickers, (str,)):
        tickers = [tickers]

    # normalize dates
    if end is None:
        end = dt.date.today()
    if isinstance(end, str):
        end = dt.date.fromisoformat(end)
    if start is None:
        # default: 3 years back if not provided
        start = end - dt.timedelta(days=365*3)
    if isinstance(start, str):
        start = dt.date.fromisoformat(start)

    frames = []
    for t in tickers:
        t = t.upper()
        cp = _cache_path(t)
        cached = None

        if use_cache and os.path.exists(cp):
            try:
                cached = pd.read_parquet(cp)
            except Exception:
                cached = None

        need_from = start
        if cached is not None and not cached.empty:
            last_cached_date = cached.index.max().date()
            # if cache already has data close to end, only fetch the gap
            if last_cached_date >= end:
                df = cached
            else:
                need_from = last_cached_date + dt.timedelta(days=1)
                fresh = yf.download(t, start=need_from.isoformat(), end=(end + dt.timedelta(days=1)).isoformat(), interval=interval, auto_adjust=False, progress=False)
                if not fresh.empty:
                    # yfinance returns single-index columns for single ticker
                    fresh.index = pd.to_datetime(fresh.index)
                    cached = pd.concat([cached, fresh[~fresh.index.isin(cached.index)]], axis=0)
                df = cached
        else:
            fresh = yf.download(t, start=start.isoformat(), end=(end + dt.timedelta(days=1)).isoformat(), interval=interval, auto_adjust=False, progress=False)
            df = fresh
            if df is not None and not df.empty:
                df.index = pd.to_datetime(df.index)

        # persist cache
        if df is not None and not df.empty and use_cache:
            try:
                df.to_parquet(cp)
            except Exception:
                pass

        # normalize to multiindex columns: (ticker, field)
        if df is None or df.empty:
            continue
        df.columns = pd.MultiIndex.from_product([[t], df.columns])
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, axis=1).sort_index()
    # Drop exact-duplicate rows if any
    out = out[~out.index.duplicated(keep="last")]
    return out

def get_close_series(ticker: str, start: str | dt.date | None = None, end: str | dt.date | None = None) -> pd.Series:
    df = get_price_history([ticker], start=start, end=end)
    if df.empty:
        return pd.Series(dtype="float64")
    return df[(ticker.upper(), "Close")].rename(ticker.upper())
