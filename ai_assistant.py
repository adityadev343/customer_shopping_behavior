import streamlit as st
import google.generativeai as genai
import re
import plotly.express as px
import pandas as pd


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
You are an advanced-expert SQL assistant with 20+ years of professional experience for a shopping behavior dataset.

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
You are a senior business analyst with 20+ years of professional experience. Below is a data result from a user's SQL query on a shopping dataset.

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

def generate_dynamic_chart(result_df: pd.DataFrame, original_question: str, api_keys: list):
    """
    Fully dynamic, context-aware chart generator.
    Uses heuristics + light Gemini call only for the title.
    """
    if result_df.empty or len(result_df) > 100 or len(result_df.columns) < 2:
        return None

    try:
        # === 1. Data Profiling ===
        numeric_cols = [col for col in result_df.columns if pd.api.types.is_numeric_dtype(result_df[col])]
        cat_cols = [col for col in result_df.columns if not pd.api.types.is_numeric_dtype(result_df[col])]
        
        # Cardinality
        cardinality = {col: result_df[col].nunique() for col in result_df.columns}
        
        # Potential x-axis candidates (low cardinality categorical)
        x_candidates = [col for col in cat_cols if cardinality[col] <= 20]
        if not x_candidates and cat_cols:
            x_candidates = cat_cols[:2]

        # Y-axis (numeric)
        y_col = numeric_cols[0] if numeric_cols else None

        # === 2. Intelligent Chart Type Decision ===
        fig = None
        chart_type = "bar"

        if y_col and x_candidates:
            x_col = x_candidates[0]
            
            # Time/Season detection
            if any(keyword in x_col.lower() for keyword in ["season", "month", "year", "date", "age"]):
                fig = px.line(result_df, x=x_col, y=y_col, title="Trend Analysis", 
                             markers=True, color_discrete_sequence=["#636EFA"])
                chart_type = "line"
            
            # High cardinality → Top N Bar
            elif cardinality[x_col] > 12:
                top_n = result_df.nlargest(12, y_col)
                fig = px.bar(top_n, x=y_col, y=x_col, orientation='h',
                           title="Top Results", color_discrete_sequence=["#636EFA"])
                chart_type = "horizontal_bar"
            
            # Standard Bar
            else:
                fig = px.bar(result_df, x=x_col, y=y_col, title="Category Comparison",
                           color=x_col if cardinality[x_col] <= 8 else None)
        
        elif len(numeric_cols) >= 2:
            # Scatter for two numerics
            fig = px.scatter(result_df, x=numeric_cols[0], y=numeric_cols[1],
                           color=cat_cols[0] if cat_cols else None,
                           title="Relationship Analysis")
            chart_type = "scatter"
        
        else:
            # Fallback
            fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1] if len(result_df.columns)>1 else None)

        if fig is None:
            return None

        # === 3. Gemini Smart Title ===
        title_prompt = f"""
        User's original question: "{original_question}"
        Result columns: {list(result_df.columns)}
        Chart type: {chart_type}
        First 3 rows summary: {result_df.head(3).to_dict(orient='records')}

        Generate ONLY a short, professional, insightful chart title (max 8-10 words).
        Make it specific to what the visualization actually shows.
        """

        smart_title = call_gemini_with_fallback(title_prompt, api_keys)
        if smart_title and len(smart_title) < 120:
            fig.update_layout(title=smart_title.strip())
        else:
            # Fallback title
            fig.update_layout(title=f"Visualization: {original_question[:80]}...")

        fig.update_layout(height=500, template="plotly_white")
        return fig

    except Exception as e:
        st.warning(f"Chart generation failed: {e}")
        return None
