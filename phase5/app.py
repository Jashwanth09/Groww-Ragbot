#!/usr/bin/env python3
"""
Phase 5: Streamlit UI Development
Complete chat interface for ICICI Prudential MF Facts Assistant
"""

import streamlit as st
import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase4'))

from enhanced_answer_generator import EnhancedAnswerGenerator

# Page config
st.set_page_config(
    page_title="ICICI Pru MF Facts Assistant",
    page_icon="🔍",
    layout="centered"
)

# Padding override
st.markdown("""
<style>
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    section[data-testid="stMain"] > div {
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔍 ICICI Prudential MF Facts Assistant")
st.caption("Powered by Groww | Facts-only, No investment advice")

# Disclaimer
st.info("""
💡 **What I can help with:**
- Expense ratios, exit loads, minimum SIP amounts
- Benchmarks, riskometer ratings
- How to download statements

❌ **What I cannot do:**
- Provide investment advice or recommendations
- Predict returns or compare performance
- Handle account/transaction issues
""")

# Scheme scope
with st.expander("📋 Covered Schemes"):
    st.markdown("""
    1. ICICI Prudential Multi Asset Fund Direct Growth
    2. ICICI Prudential Large Cap Fund Direct Growth
    3. ICICI Prudential Nifty Next 50 Index Direct Growth
    4. ICICI Prudential Large & Mid Cap Fund Direct Plan Growth
    """)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sample_query" not in st.session_state:
    st.session_state.sample_query = None

# Sample Questions Section
st.markdown("### 💬 Try asking:")

col1, col2 = st.columns(2)

with col1:
    if st.button("What is the expense ratio of ICICI Pru Large Cap Fund?"):
        st.session_state.sample_query = "What is the expense ratio of ICICI Pru Large Cap Fund?"
    
    if st.button("Exit load for Multi Asset Fund?"):
        st.session_state.sample_query = "Exit load for Multi Asset Fund?"

with col2:
    if st.button("Minimum SIP for Nifty Next 50 Index Fund?"):
        st.session_state.sample_query = "Minimum SIP for Nifty Next 50 Index Fund?"
    
    if st.button("How to download capital gains statement?"):
        st.session_state.sample_query = "How to download capital gains statement?"

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message["role"] == "assistant" and "sources" in message:
            if message["sources"]:
                with st.expander("📎 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"- {source}")

# Handle sample query clicks
if st.session_state.sample_query:
    user_query = st.session_state.sample_query
    st.session_state.sample_query = None  # Reset
else:
    user_query = st.chat_input("Ask about ICICI Prudential schemes...")

# Process user query
if user_query:
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })
    
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                # Initialize enhanced answer generator
                generator = EnhancedAnswerGenerator()
                response = generator.generate_answer(user_query)
                
                answer = response.get("answer", "I apologize, but I couldn't process your query. Please try again.")
                sources = response.get("citations", [])
                
                st.markdown(answer)
                
                # Show sources
                if sources:
                    with st.expander("📎 Sources"):
                        for source in sources:
                            st.markdown(f"- {source}")
            except Exception as e:
                st.error(f"Error processing your query: {str(e)}")
                answer = "I encountered an error processing your query. Please try again later."
                sources = []
        
        st.markdown(answer)
        
        # Show sources
        if sources:
            with st.expander("📎 Sources"):
                for source in sources:
                    st.markdown(f"- {source}")
    
    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

# Sidebar Information
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant provides **factual information only** about 4 ICICI Prudential Direct Growth schemes.
    
    **Last updated:** April 2024
    
    **Data sources:**
    - ICICI Prudential AMC official website
    - SEBI-mandated disclosures (KIM/SID)
    - Groww platform
    - AMFI/SEBI investor education
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("""
    This tool is for informational purposes only and does not constitute investment advice.
    
    Mutual fund investments are subject to market risks. Please read all scheme-related documents carefully before investing.
    
    For personalized advice, consult a SEBI-registered investment advisor.
    """)
    
    st.markdown("---")
    
    # Feedback
    st.markdown("### 📧 Feedback")
    if st.button("Report an issue"):
        st.info("Contact: support@icicipruamc.com")

# Clear Chat Button
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Debug Mode (Optional)
if st.sidebar.checkbox("🐛 Debug Mode", value=False):
    with st.sidebar.expander("Last Response Details"):
        if st.session_state.messages:
            last_response = st.session_state.messages[-1]
            st.json(last_response)
