"""
Simple Groww Chatbot - Minimal Working Version
"""

import streamlit as st

st.set_page_config(
    page_title="Groww Chatbot",
    page_icon="🌱",
    layout="centered"
)

st.markdown("""
<style>
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    section[data-testid="stMain"] > div {
        padding: 0 !important;
    }
    .chat-header {
        background: linear-gradient(135deg, #00D26A 0%, #00A859 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <h2>🌱 Groww Assistant</h2>
    <p>Online</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Quick Actions")

if st.button("What is SIP?"):
    st.info("SIP (Systematic Investment Plan) is a smart way to invest in mutual funds.")

if st.button("How to invest?"):
    st.info("Getting started is easy! Download the app, complete KYC, add funds, and start investing.")

st.markdown("### Type your question")
user_input = st.text_input("Ask me anything about investments...")

if st.button("Send"):
    if user_input:
        st.success(f"You asked: {user_input}")
        st.info("I'm here to help with your investment queries!")
