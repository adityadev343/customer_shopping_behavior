import streamlit as st
import duckdb
from ai_assistant import (
    get_gemini_api_keys,
    call_gemini_with_fallback,
    get_schema_description,
    build_sql_generation_prompt,
    parse_sql_from_response,
    build_insight_prompt,
    generate_dynamic_chart,
)

def render_ai_sql_tab(df, next_key):
    st.subheader("🤖 Ask a business question in plain English")

    # Get API keys (from st.secrets)
    api_keys = get_gemini_api_keys()
    if not api_keys:
        st.warning("No Gemini API keys found. Please set GEMINI_API_KEY_1, etc. in .streamlit/secrets.toml")
        api_keys = ["dummy"]  # fallback to avoid errors

    schema_text = get_schema_description(df)  # use full df for schema

    user_question = st.text_area(
        "Please write here:",
        placeholder="Example: Show me total revenue by category for female customers in California",
        height=100,
    )

    col_gen, col_clear = st.columns(2)
    with col_gen:
        if st.button("✨ Generate SQL", use_container_width=True):
            if not user_question.strip():
                st.error("Please enter a question first.")
            else:
                prompt = build_sql_generation_prompt(user_question, schema_text)
                with st.spinner("Processing..."):
                    response = call_gemini_with_fallback(prompt, api_keys)
                    if response:
                        refusal_phrases = [
                            "Please ask a relevant business question",
                            "I cannot answer this because the dataset lacks",
                        ]
                        is_refusal = any(phrase in response for phrase in refusal_phrases)
                        if is_refusal:
                            st.warning(response)
                        else:
                            generated_sql = parse_sql_from_response(response)
                            st.session_state["generated_sql"] = generated_sql
                            st.session_state["sql_editor"] = generated_sql
                            st.success("SQL generated successfully! You can edit it below.")
                            st.rerun()
                    else:
                        st.error("All API keys failed. Please check your keys and try again.")

    with col_clear:
        if st.button("🗑️ Clear SQL", use_container_width=True):
            st.session_state.pop("generated_sql", None)
            st.session_state.pop("sql_editor", None)
            st.rerun()

    if "sql_editor" not in st.session_state:
        if "generated_sql" in st.session_state:
            st.session_state["sql_editor"] = st.session_state["generated_sql"]
        else:
            st.session_state["sql_editor"] = "SELECT * FROM df LIMIT 10"

    sql_query = st.text_area("SQL Query (editable)", key="sql_editor", height=150)

    if st.button("▶️ Execute Query", use_container_width=True):
        if not sql_query.strip():
            st.error("SQL query is empty.")
        else:
            try:
                conn = duckdb.connect()
                conn.register("df", df)
                result_df = conn.execute(sql_query).fetchdf()
                
                st.success(f"Query returned {len(result_df):,} rows.")

                # Result table
                st.dataframe(result_df, use_container_width=True)

                # Dynamic visualization
                if not result_df.empty and len(result_df.columns) >= 2 and len(result_df) <= 100:
                    with st.spinner("🎨 Generating smart visualization..."):
                        fig = generate_dynamic_chart(result_df, user_question, api_keys)
                        if fig:
                            st.subheader("📊 Smart Visualization")
                            st.plotly_chart(fig, use_container_width=True, key=next_key("ai_dynamic_viz"))
                        else:
                            st.info("Visualization not available for this result shape.")

                # AI Insights
                if not result_df.empty and len(result_df) <= 50:
                    with st.spinner("🤖 Generating business insights..."):
                        insight_prompt = build_insight_prompt(user_question, result_df)
                        insight_response = call_gemini_with_fallback(insight_prompt, api_keys)
                        if insight_response:
                            st.info(f"💼 **Business Insights:**\n\n{insight_response}")
                elif len(result_df) > 50:
                    st.info("📊 Result is large (>50 rows). AI insights skipped. Try adding LIMIT or GROUP BY.")

            except Exception as e:
                st.error(f"SQL execution error: {e}")

    st.markdown("---")
    st.caption("💡 Tip: You can manually edit the SQL before executing.")