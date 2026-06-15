import streamlit as st
import pandas as pd
import numpy as np
from config import DATA_FILE


@st.cache_data
def load_data():
    """Load and preprocess the shopping behavior dataset."""
    df = pd.read_csv(DATA_FILE)

    # Create age_group if missing
    if "age_group" not in df.columns:
        bins = [17, 30, 45, 60, np.inf]
        labels = ["18-30", "31-45", "46-60", "61+"]
        df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=True)

    # Ensure numeric types
    df["purchase_amount"] = df["purchase_amount"].astype(float)
    df["review_rating"] = df["review_rating"].astype(float)

    # Customer segment based on previous purchases
    def segment(prev):
        if prev <= 1:
            return "New"
        elif prev <= 5:
            return "Returning"
        else:
            return "Loyal"

    df["segment"] = df["previous_purchases"].apply(segment)

    return df