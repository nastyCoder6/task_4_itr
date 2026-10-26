from pathlib import Path

import streamlit as st

from agent import DataAgent
from pipeline import DataPipeline

st.set_page_config(page_title="TASK_4", layout="wide")
st.title("Book Store Analysis")

selected_store = st.selectbox(
    "Select Store", ["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]
)
BASE_DIR = Path(__file__).parent
STORE_DIR = BASE_DIR / "data" / selected_store

pipeline = DataPipeline(STORE_DIR)
books, orders, users, metrics = pipeline.run()
agent = DataAgent(books, orders, users)

st.divider()

tab1, tab2, tab3 = st.tabs(["Overview", "Top Revenue Days", "Daily Revenue Chart"])

with tab1:
    st.subheader(f"Customer & Author Metrics ({selected_store})")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Number of Unique Users", value=metrics["total_unique_users"])
        st.metric(label="Unique Sets of Authors", value=metrics["unique_authors"])

    with col2:
        st.metric(label="Most Popular Author(s)", value=f"{metrics['top_author']}")
        st.write(f"Best Buyer: {metrics['top_customer'][0]}")
        st.code(metrics["top_customer"][1], language="json")

with tab2:
    st.subheader(f"Top 5 Days by Revenue ({selected_store})")
    col1, col2 = st.columns([1, 5])
    with col1:
        st.dataframe(metrics["top_5_revenue"])

    with col2:
        st.bar_chart(metrics["top_5_revenue"])

with tab3:
    st.subheader(f"Daily Revenue Chart ({selected_store})")
    st.line_chart(metrics["daily_revenue"], x_label="Date", y_label="Revenue")


st.divider()
st.subheader("Assistant Chat")
st.markdown(
    """
    Dynamically access source data for a given store and filter them."""
)
if prompt := st.chat_input("Ask for data (e.g., 'Show me orders from 2025')..."):
    with st.chat_message("user"):
        st.write(f"User: {prompt}")
    with st.chat_message("assistant"):
        with st.status("Proccessing data...", state="running", expanded=True):
            st.write(agent.process_query(prompt))
            st.success("Done!")
            st.balloons()
