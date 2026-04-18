"""
ICICI Prudential Mutual Fund RAG System - Streamlit Web Interface
Phase 4.2: Streamlit Web Interface
"""

import streamlit as st
import sys
import os
from datetime import datetime
import json

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))

from llm_config import LLMConfig, setup_logging
from answer_generator import AnswerGenerator

# Configure Streamlit page
st.set_page_config(
    page_title="ICICI Prudential Mutual Fund FAQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .scheme-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .answer-box {
        background: #e8f4fd;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .query-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'answer_generator' not in st.session_state:
        st.session_state.answer_generator = None
    if 'config_valid' not in st.session_state:
        st.session_state.config_valid = False

def load_answer_generator():
    """Load answer generator with configuration"""
    try:
        config = LLMConfig.from_env()
        if config.validate():
            st.session_state.answer_generator = AnswerGenerator(config)
            st.session_state.config_valid = True
            return True
        else:
            st.session_state.config_valid = False
            return False
    except Exception as e:
        st.session_state.config_valid = False
        st.error(f"Configuration error: {e}")
        return False

def display_header():
    """Display application header"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 ICICI Prudential Mutual Fund FAQ</h1>
        <p>Get accurate answers about ICICI Prudential Direct Growth schemes with AI-powered assistance</p>
    </div>
    """, unsafe_allow_html=True)

def display_scheme_info():
    """Display supported schemes information"""
    st.markdown("### 🎯 Supported Schemes")
    
    schemes = [
        "ICICI Prudential Dynamic Plan Direct Growth",
        "ICICI Prudential Large Cap Fund Direct Growth", 
        "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
        "ICICI Prudential Top 100 Fund Direct Growth"
    ]
    
    for scheme in schemes:
        st.markdown(f"""
        <div class="scheme-card">
            <strong>✅ {scheme}</strong>
        </div>
        """, unsafe_allow_html=True)

def display_sidebar():
    """Display sidebar with information and settings"""
    with st.sidebar:
        st.markdown("## ℹ️ About This Assistant")
        st.markdown("""
        I can help you with factual information about:
        - 📈 Expense ratios
        - 💰 Exit loads
        - 📊 Minimum SIP/lumpsum amounts
        - 🎯 Benchmark indices
        - ⚠️ Riskometer ratings
        - 📋 Asset allocation
        - 📄 Statement downloads
        """)
        
        st.markdown("---")
        
        st.markdown("## ❌ What I Cannot Do")
        st.markdown("""
        - 🚫 Investment advice/recommendations
        - 🚫 Return predictions
        - 🚫 Account/transaction support
        - 🚫 Other AMC schemes
        """)
        
        st.markdown("---")
        
        st.markdown("## 🔗 Useful Links")
        st.markdown("""
        - [📚 SEBI Investor Awareness](https://investor.sebi.gov.in)
        - [👥 SEBI Registered Advisors](https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes)
        - [🌐 Groww Support](https://support.groww.in)
        - [🏢 ICICI Prudential](https://www.icicipruamc.com)
        """)
        
        if st.session_state.config_valid:
            st.markdown("---")
            st.success("✅ LLM Configuration Valid")
        else:
            st.markdown("---")
            st.error("❌ LLM Configuration Invalid")
            st.markdown("Please check your API keys in Streamlit secrets.")

def display_chat_history():
    """Display chat history"""
    if st.session_state.chat_history:
        st.markdown("### 💬 Chat History")
        
        for i, chat in enumerate(st.session_state.chat_history):
            with st.container():
                # Query
                st.markdown(f"""
                <div class="query-box">
                    <strong>👤 You:</strong> {chat['query']}
                    <br><small>🕒 {chat['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Answer
                answer_type = chat.get('type', 'unknown')
                confidence = chat.get('confidence', 'unknown')
                
                if answer_type == 'out_of_scope_refusal':
                    st.markdown(f"""
                    <div class="error-box">
                        <strong>🤖 Assistant:</strong> {chat['answer']}
                        <br><small>🏷️ Type: Out of Scope | 🔍 Confidence: {confidence}</small>
                    </div>
                    """, unsafe_allow_html=True)
                elif answer_type == 'error':
                    st.markdown(f"""
                    <div class="error-box">
                        <strong>🤖 Assistant:</strong> {chat['answer']}
                        <br><small>🏷️ Type: Error | 🔍 Confidence: {confidence}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="answer-box">
                        <strong>🤖 Assistant:</strong> {chat['answer']}
                        <br><small>🏷️ Type: {answer_type} | 🔍 Confidence: {confidence} | ⏱️ {chat.get('processing_time', 0):.2f}s</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")

def clear_chat_history():
    """Clear chat history"""
    st.session_state.chat_history = []

def main():
    """Main application function"""
    initialize_session_state()
    
    # Load answer generator
    if not st.session_state.answer_generator:
        load_answer_generator()
    
    display_header()
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 💭 Ask Your Question")
        
        # Query input
        query = st.text_input(
            "Enter your question about ICICI Prudential schemes:",
            placeholder="e.g., What is the expense ratio of ICICI Prudential Large Cap Fund?",
            key="query_input"
        )
        
        # Buttons
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            submit_button = st.button("🚀 Ask", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Clear History", use_container_width=True)
        
        if clear_button:
            clear_chat_history()
            st.rerun()
        
        # Process query
        if submit_button and query:
            if not st.session_state.config_valid:
                st.error("⚠️ LLM configuration is invalid. Please check your API keys.")
                return
            
            with st.spinner("🤔 Thinking..."):
                try:
                    result = st.session_state.answer_generator.generate_answer(query)
                    
                    # Add to chat history
                    chat_entry = {
                        'query': query,
                        'answer': result['answer'],
                        'type': result['type'],
                        'confidence': result['confidence'],
                        'processing_time': result.get('processing_time', 0),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.session_state.chat_history.append(chat_entry)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing query: {e}")
        
        # Display chat history
        display_chat_history()
    
    with col2:
        display_scheme_info()
    
    # Display sidebar
    display_sidebar()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p><strong>📊 ICICI Prudential Mutual Fund FAQ System</strong></p>
        <p>Powered by AI | Data sourced from ICICI Prudential and Groww</p>
        <p><small>⚠️ This is for informational purposes only. Not investment advice.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
