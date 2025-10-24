#!/usr/bin/env python3
"""
market_interactive.py

Interactive, artisan-focused MAM pipeline that uses pytrends for real-time signals.
No fallbacks: if pytrends cannot return data the script will stop with an error.

Outputs (in output directory you provide):
 - timeseries_live.csv
 - analytics_live.csv
 - gemini_analysis.jsonl   (only if you elect to call Gemini)

Run:
  python market_interactive.py

Dependencies:
  pip install pandas numpy requests pytrends python-dateutil google-genai
"""
import os
import sys
import json
import time
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import numpy as np
import pandas as pd

# pytrends
try:
    from pytrends.request import TrendReq
except Exception as e:
    sys.exit("pytrends is required. Install with: pip install pytrends")

# optional google genai
HAS_GENAI = False
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

# -------------------------
# Utilities
# -------------------------
def iso_dates_back(days: int):
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    return pd.date_range(start, end, freq='D')

def pct_change_safe(a, b):
    try:
        a = float(a); b = float(b)
    except Exception:
        return float('nan')
    if a == 0:
        return float('nan')
    return (b - a) / float(abs(a))

def ewma_forecast(series: pd.Series, alpha: float = 0.25, horizon: int = 7) -> List[float]:
    if series is None or len(series) == 0:
        return [0.0] * horizon
    s = series.ffill().fillna(0.0)
    ema = float(s.iloc[0])
    ema_vals = [ema]
    for v in s.iloc[1:]:
        ema = alpha * float(v) + (1 - alpha) * ema
        ema_vals.append(ema)
    if len(ema_vals) == 1:
        return [float(ema_vals[-1])] * horizon
    slope = ema_vals[-1] - ema_vals[-2]
    return [float(max(0.0, ema_vals[-1] + slope * (i + 1))) for i in range(horizon)]

def seasonality_score_weekday(series: pd.Series) -> float:
    if series is None or series.empty:
        return 0.0
    df = pd.DataFrame({'date': series.index, 'v': series.values})
    df['dow'] = df['date'].dt.weekday
    means = df.groupby('dow')['v'].mean()
    amp = float(means.max() - means.min())
    overall = float(max(series.mean(), 1e-6))
    return float(min(1.0, amp / overall))

# -------------------------
# Pytrends fetch (no synthetic fallback)
# -------------------------
def _explicit_date_range(days: int) -> str:
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)
    return f"{start_date.isoformat()} {end_date.isoformat()}"

def fetch_trends_for_keyword(keyword: str, days: int, region: str, retries: int = 3, wait_s: float = 2.0) -> pd.DataFrame:
    """
    Fetch Google Trends interest_over_time for a single keyword and region.
    If repeatedly fails, raise an exception (NO fallbacks).
    """
    timeframe = _explicit_date_range(days)
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            py = TrendReq(hl='en-US', tz=0)
            py.build_payload([keyword], timeframe=timeframe, geo=region)
            df = py.interest_over_time()
            if df.empty:
                raise RuntimeError(f"pytrends returned empty dataframe for keyword='{keyword}' region='{region}' timeframe='{timeframe}'")
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])
            # sum or take the column — for single keyword the single column is present; we'll sum anyway for robustness
            series = df.sum(axis=1).rename('interest')
            # ensure full index presence
            full_idx = iso_dates_back(days)
            series = series.reindex(full_idx)
            return series.to_frame()
        except Exception as e:
            last_err = e
            if attempt < retries:
                sleep = wait_s * (2 ** (attempt - 1))
                print(f"[pytrends] attempt {attempt} for '{keyword}' failed: {e}. Retrying in {sleep:.1f}s...")
                time.sleep(sleep)
            else:
                print(f"[pytrends] attempt {attempt} for '{keyword}' failed: {e}. No more retries.")
    raise RuntimeError(f"pytrends failed for keyword='{keyword}' region='{region}' after {retries} attempts. Last error: {last_err}")

# -------------------------
# Gemini integration: very detailed artisan prompt and structured JSON reply
# -------------------------
def call_gemini_structured(summary_text: str, api_key: str, model: str = "gemini-2.5-flash"):
    """
    Use google.genai (gemini) to request a structured JSON analysis tailored for artisan projects.
    The model is asked to return only a JSON object with fields:
      - trend_score (0..1)
      - detailed_analysis (string)
      - suggested_actions (array of strings)
      - recommended_hashtags (array of strings)
      - demand_estimate (object with 'short_term' and 'medium_term' numeric estimates)
      - pricing_advice (string)
      - inventory_advice (string)
    If parsing fails, raise.
    """
    if not HAS_GENAI:
        raise RuntimeError("google.genai package not installed; cannot call Gemini via genai.")
    client = genai.Client(api_key=api_key)
    prompt = (
        "You are an expert marketplace analyst specialized in artisan and handcrafted products.\n"
        "You will be given a short summary with numeric signals (recent interest metrics, seasonality score) for a product keyword.\n"
        "Return ONLY a JSON object (in strict JSON, no surrounding commentary) with the following keys:\n"
        "  - trend_score: a number between 0 and 1 (higher means stronger rising interest)\n"
        "  - detailed_analysis: a multi-paragraph string (2-4 paragraphs) explaining demand drivers and audience for artisan contexts\n"
        "  - suggested_actions: an array of short actionable strings for artisans (pricing, channels, promotions, partnerships)\n"
        "  - recommended_hashtags: an array of 6-12 suggested social hashtags tailored to artisan audiences\n"
        "  - demand_estimate: an object with numeric 'short_term' (7-day) and 'medium_term' (30-day) relative demand multipliers (floats where 1.0 = baseline)\n"
        "  - pricing_advice: a short string with recommended price positioning and margin considerations for artisans\n"
        "  - inventory_advice: a short string with reorder/safety-stock suggestions for small artisan operations\n"
        "\nSUMMARY:\n"
        + summary_text +
        "\n\nReturn only the JSON object and nothing else."
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=800, thinking_config=types.ThinkingConfig(thinking_budget=0))
    )
    text = getattr(response, "text", None) or str(response)
    text = text.strip()
    # Try to find JSON substring
    import re
    m = re.search(r'(\{.*\})', text, flags=re.S)
    if not m:
        raise RuntimeError("Gemini response did not contain a JSON object.")
    json_text = m.group(1)
    # parse
    try:
        parsed = json.loads(json_text)
        return parsed
    except Exception as e:
        raise RuntimeError(f"Failed to parse Gemini JSON response: {e}\nRaw text:\n{json_text}")

# -------------------------
# Main interactive flow
# -------------------------
def interactive_prompt():
    print("=== Artisan Market Analytics (interactive) ===")
    kws = input("Enter one or more keywords (comma-separated), e.g. 'handmade pottery, handloom saree': ").strip()
    if not kws:
        print("No keywords provided. Exiting.")
        sys.exit(1)
    keywords = [k.strip() for k in kws.split(",") if k.strip()]
    regions_raw = input("Enter regions (Google Trends geo codes), comma-separated (default 'US'): ").strip()
    regions = [r.strip() for r in regions_raw.split(",") if r.strip()] if regions_raw else ["US"]
    days_raw = input("Enter number of days history to fetch (e.g., 60): ").strip()
    try:
        days = int(days_raw) if days_raw else 60
        if days < 1 or days > 365:
            raise ValueError("days must be 1..365")
    except Exception as e:
        print("Invalid days:", e)
        sys.exit(1)
    out_dir = input("Enter output directory (will be created if missing), e.g. 'results': ").strip()
    if not out_dir:
        print("No output directory provided. Exiting.")
        sys.exit(1)
    use_gemini = input("Call Gemini for detailed artisan analysis? (y/N): ").strip().lower() == 'y'
    gemini_key = None
    if use_gemini:
        # try environment first
        gemini_key = "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4"
        if not gemini_key:
            gemini_key = input("Enter GEMINI API key (or set GEMINI_API_KEY env var): ").strip()
        # final check
        if not gemini_key:
            print("No Gemini API key provided; Gemini disabled.")
            use_gemini = False
    return keywords, regions, days, out_dir, use_gemini, gemini_key

def main():
    keywords, regions, days, out_dir, use_gemini, gemini_key = interactive_prompt()
    os.makedirs(out_dir, exist_ok=True)

    timeseries_rows = []
    analytics_rows = []
    gemini_output_path = os.path.join(out_dir, "gemini_analysis.jsonl") if use_gemini else None

    for kw in keywords:
        for reg in regions:
            print(f"\nFetching trends for keyword='{kw}' region='{reg}' (days={days}) ...")
            series_df = fetch_trends_for_keyword(kw, days, reg, retries=3, wait_s=2.0)
            series = series_df['interest'].astype(float)
            series.index = pd.to_datetime(series.index)

            # EWMA forecasts
            fc7 = ewma_forecast(series, alpha=0.25, horizon=7)
            fc30 = ewma_forecast(series, alpha=0.20, horizon=30)
            fc90 = ewma_forecast(series, alpha=0.15, horizon=90)

            season_score = seasonality_score_weekday(series)
            recent7_mean = float(series.tail(7).mean()) if len(series) >= 7 else float(series.mean())
            recent14_mean = float(series.tail(14).mean()) if len(series) >= 14 else recent7_mean
            pct7 = pct_change_safe(float(series.iloc[-8]) if len(series) > 8 else series.iloc[0], float(series.iloc[-1]))

            # prepare summary for Gemini or internal heuristic
            summary_text = (
                f"Keyword: {kw}\nRegion: {reg}\nDays: {days}\n"
                f"Recent 7-day mean interest: {recent7_mean:.3f}\n"
                f"Recent 14-day mean interest: {recent14_mean:.3f}\n"
                f"7-day percent change (approx): {pct7:.3f}\n"
                f"seasonality_score: {season_score:.3f}\n"
            )

            # Gemini analysis (if requested)
            gemini_analysis = None
            if use_gemini:
                try:
                    print("Calling Gemini for detailed artisan analysis (this may take a few seconds)...")
                    gemini_analysis = call_gemini_structured(summary_text, api_key=gemini_key)
                    # write to jsonl (append)
                    with open(gemini_output_path, 'a', encoding='utf-8') as gf:
                        entry = {
                            'keyword': kw,
                            'region': reg,
                            'days': days,
                            'summary': summary_text,
                            'analysis': gemini_analysis
                        }
                        gf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    trend_score = float(gemini_analysis.get('trend_score') or 0.0)
                    trend_explanation = gemini_analysis.get('detailed_analysis', '')[:1000]
                except Exception as e:
                    print("Gemini call or parse failed:", e)
                    print("Aborting (no fallbacks).")
                    raise
            else:
                # heuristic trend score
                recent_norm = min(1.0, recent14_mean / max(1.0, series.max()))
                trend_score = float(min(1.0, 0.7 * recent_norm + 0.3 * season_score))
                trend_explanation = "Heuristic artisan-focused interpretation: recent interest blended with weekday seasonality."

            # record analytics
            analytics_rows.append({
                'keyword': kw,
                'region': reg,
                'fc7_median': float(np.median(fc7)),
                'fc30_median': float(np.median(fc30)),
                'fc90_median': float(np.median(fc90)),
                'recent_7_mean': recent7_mean,
                'recent_14_mean': recent14_mean,
                'seasonality_score': float(season_score),
                'trend_score': float(trend_score),
                'trend_explanation': trend_explanation
            })

            # record timeseries rows
            df = pd.DataFrame({'date': series.index, 'interest': series.values})
            df['ewma_7'] = df['interest'].ewm(span=7, adjust=False).mean()
            df['rolling_7'] = df['interest'].rolling(7, min_periods=1).mean()
            df['keyword'] = kw
            df['region'] = reg
            timeseries_rows.append(df)

            # polite pause between keywords/regions
            time.sleep(0.5)

    # write outputs
    ts_out = os.path.join(out_dir, 'timeseries_live.csv')
    ana_out = os.path.join(out_dir, 'analytics_live.csv')

    timeseries_df = pd.concat(timeseries_rows, ignore_index=True) if timeseries_rows else pd.DataFrame()
    analytics_df = pd.DataFrame(analytics_rows)

    timeseries_df.to_csv(ts_out, index=False)
    analytics_df.to_csv(ana_out, index=False)

    print(f"\nWrote timeseries -> {ts_out}")
    print(f"Wrote analytics  -> {ana_out}")
    if use_gemini:
        print(f"Wrote Gemini analyses -> {gemini_output_path}")

    print("\nSample analytics (top rows):")
    if not analytics_df.empty:
        print(analytics_df.head().to_string(index=False))
    else:
        print("(no analytics rows)")

if __name__ == '__main__':
    main()
