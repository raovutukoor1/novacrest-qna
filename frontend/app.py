import streamlit as st
import requests
import os

# Fallback to the backend service name on the shared Docker network
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")

st.set_page_config(page_title="NovaCrest", page_icon="🏨", layout="wide")

with st.sidebar:
    st.header("⚙️ Parameters")
    k = st.slider("k (chunks to retrieve)", min_value=1, max_value=10, value=2)
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
    max_tokens = st.slider("Max tokens", min_value=64, max_value=2048, value=512, step=64)

st.title("🏨 NovaCrest")
st.write("Ask a question about Salesforce manuals.")
response_type = st.radio("Response mode", ["Answer only", "Answer + Relevant Chunks"], horizontal=True)
query = st.text_input("Your question", placeholder="e.g., Can I use Salesforce on mobile devices?")

if st.button("Submit", type="primary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        endpoint = "/v1/answer" if response_type == "Answer only" else "/v1/answer_with_relevant_chunks"
        payload = {"query": query, "k": k, "temperature": temperature, "max_tokens": max_tokens}
        headers = {}
        if BACKEND_API_KEY:
            headers["X-API-Key"] = BACKEND_API_KEY
        try:
            with st.spinner("Thinking..."):
                response = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                st.subheader("Answer")
                st.write(result["answer"])
                if response_type == "Answer + Relevant Chunks":
                    st.subheader("Relevant Chunks")
                    for i, chunk in enumerate(result["relevant_chunks"], start=1):
                        with st.expander(f"Chunk {i}"):
                            st.write(chunk)
            else:
                st.error(f"Unable to get response. Status: {response.status_code}")
        except Exception:
            st.error(f"Unable to connect to the RAG API at {BACKEND_URL}. Please verify your network and backend settings.")
