import pandas as pd
from typing import List, Optional, Literal

from data_viz import settings


def summarize_chart(
    df: pd.DataFrame,
    chart_type: str,
    x: Optional[str] = None,
    y1: Optional[List[str]] = None,
    y2: Optional[List[str]] = None,
    title: str = "",
    provider: Literal["openai", "anthropic", "gemini", "groq"] = "groq",
    client=None,
    model: str = None,
) -> str:
    """
    Generate an LLM-powered summary of a chart based on its underlying data.

    Args:
        df (pd.DataFrame): Chart dataframe.
        chart_type (str): e.g. "line", "bar", "scatter".
        x (str): X-axis column.
        y1 (list[str]): Primary Y-axis series.
        y2 (list[str]): Secondary Y-axis series.
        title (str): Chart title.
        provider (str): LLM provider name.
        client: Pre-initialised client (OpenAI, Anthropic, Google, Groq).
        model (str): Model name for that provider.

    Returns:
        str: Natural-language summary.
    """

    # ---- 1) Create compact data preview (avoid sending huge frames) ----
    df_preview = df.head(50).to_dict(orient="list")

    meta = {
        "chart_type": chart_type,
        "title": title,
        "x": x,
        "y1": y1,
        "y2": y2,
        "columns": list(df.columns),
        "data_preview": df_preview,
    }

    # ---- 2) Universal prompt ----
    prompt = f"""
    You are a data analysis assistant.
    Summarize the insights of the chart described below.
    Focus on trends, comparisons, anomalies, peaks, correlations, and interesting findings.

    Chart metadata:
    {meta}

    Write a concise, clear summary (around 4–7 sentences).
    """

    # ================
    # PROVIDER ROUTING
    # ================

    # ---- OpenAI ----
    if provider == "openai":
        if client is None:
            from openai import OpenAI
            client = OpenAI()

        model = model or "gpt-4.1-mini"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"]

    # ---- Anthropic ----
    elif provider == "anthropic":
        if client is None:
            import anthropic
            client = anthropic.Anthropic()

        model = model or "claude-3-5-sonnet-latest"

        response = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    # ---- Google Gemini ----
    elif provider == "gemini":
        if client is None:
            from google import generativeai as genai
            genai.configure(api_key="YOUR_KEY")
            client = genai

        model = model or "gemini-2.0-flash"
        response = client.GenerativeModel(model).generate_content(prompt)
        return response.text

    # ---- GROQ (Free Llama 3.1) ----
    elif provider == "groq":
        if client is None:
            from groq import Groq
            client = Groq()

        model = model or "llama-3.1-8b-instant"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


    else:
        raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    df = pd.DataFrame({
        "date": pd.date_range(start="2023-01-01", periods=12, freq="M"),
        "sales": [150, 200, 250, 300, 280, 320, 400, 450, 500, 550, 600, 700],
    })
    settings.load_settings()
    summary = summarize_chart(
        df,
        chart_type="line",
        x="date",
        y1=["sales"],
        title="Monthly Sales",
        provider="groq",   # <= try Groq for free
    )
    print(summary)
