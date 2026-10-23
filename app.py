from pathlib import Path

import streamlit as st

from pipeline import DataPipeline

st.set_page_config(page_title="TASK_4", layout="wide")
st.title("Book Store Analysis")

selected_store = st.selectbox(
    "Select Store", ["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]
)
BASE_DIR = Path(__file__).parent
STORE_DIR = BASE_DIR / "data" / selected_store

pipeline = DataPipeline(STORE_DIR)
clean_books, clean_orders, clean_users, report = pipeline.run()

st.divider()

tab1, tab2, tab3 = st.tabs(["Overview", "Top Revenue Days", "Daily Revenue Chart"])

with tab1:
    st.subheader(f"Customer & Author Metrics ({selected_store})")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Number of Unique Users", value=report["total_unique_users"])
        st.metric(label="Unique Sets of Authors", value=report["unique_authors"])

    with col2:
        st.metric(label="Most Popular Author(s)", value=f"{report['top_author']}")
        st.write(f"Best Buyer: {report['top_customer'][0]}")
        st.code(report["top_customer"][1], language="json")

with tab2:
    st.subheader(f"Top 5 Days by Revenue ({selected_store})")
    st.write(report["top_5_revenue"])
with tab3:
    st.subheader(f"Daily Revenue Chart ({selected_store})")
    st.line_chart(report["daily_revenue"])


# chat area
st.divider()
st.subheader("Assistant Chat")
if prompt := st.chat_input("Ask a question about the data..."):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write("Chat logic placeholder...")
