import streamlit as st
import google.generativeai as genai
import re


def get_gemini_api_keys():
    """Retrieve Gemini API keys from Streamlit secrets."""
    keys = []
    for i in range(1, 6):
        key_name = f"GEMINI_API_KEY_{i}"
        try:
            key = st.secrets.get(key_name)
            if key:
                keys.append(key)
        except Exception:
            pass
    return keys


def call_gemini_with_fallback(prompt, api_keys):
    """Try multiple API keys until one works."""
    for idx, key in enumerate(api_keys):
        if key == "dummy":
            continue
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            if hasattr(response, "text"):
                return response.text
            return str(response)
        except Exception as e:
            st.warning(f"API key {idx+1} failed: {e}. Trying next...")
            continue
    return None


def get_schema_description(df):
    """Generate a textual description of the dataframe schema for prompting."""
    lines = ["Table name: df", "Columns:"]
    for col in df.columns:
        if df[col].dtype == "object":
            unique_vals = df[col].dropna().unique()[:15].tolist()
            lines.append(f"- {col} (categorical): {unique_vals}")
        else:
            lines.append(f"- {col} (numeric): range [{df[col].min()}, {df[col].max()}]")
    return "\n".join(lines)


def build_sql_generation_prompt(question, schema_text):
    """Build the prompt for SQL generation."""
    return f"""
You are an expert SQL assistant for a shopping behavior dataset.

Database schema (only these columns exist, DO NOT invent any others):
{schema_text}

The user's question is:
"{question}"

Rules:
1. If the user is greeting, chatting, or asking something unrelated to the dataset:
Return EXACTLY:
Please ask a relevant business question about the shopping data.

2. If the question requires columns that do not exist:
Return EXACTLY:
I cannot answer this because the dataset lacks the necessary data.

3. Otherwise:
Generate a DuckDB SQL query.

Requirements:
- Use ONLY columns from the schema.
- Return ONLY SQL.
- Wrap the SQL in a ```sql block.
- No explanation.
"""


def parse_sql_from_response(response):
    """Extract SQL from the model's response (```sql block)."""
    match = re.search(r"```sql\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return response.strip()


def build_insight_prompt(question, result_df):
    """Build the prompt for generating business insights from query results."""
    if len(result_df) > 10:
        data_for_ai = result_df.head(10).to_string()
        note = "(showing first 10 rows due to size)"
    else:
        data_for_ai = result_df.to_string()
        note = ""

    return f"""
You are a senior business analyst. Below is a data result from a user's SQL query on a shopping dataset.

User's original question: "{question}"

Result data (max 50 rows):
{data_for_ai}
{note}

Instructions:
- Provide exactly 2–3 short bullet points of **business-level insights**.
- Do NOT repeat the raw data.
- Do NOT hallucinate numbers or trends not evident in the data.
- If the data is insufficient for a confident insight, say "Insufficient data to draw a business conclusion."
- Keep language professional, concise, and actionable.

Output format: plain text bullet points.
"""