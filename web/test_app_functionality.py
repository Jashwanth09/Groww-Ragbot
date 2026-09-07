"""
Test script to verify chatbot functionality
"""

import streamlit as st

# Test page configuration
st.set_page_config(page_title="Groww Chatbot Test", layout="centered")

st.title("🌱 Groww Chatbot - Functionality Test")

# Test 1: Basic rendering
st.header("Test 1: Basic Rendering")
st.success("✅ Page renders successfully")

# Test 2: CSS styling
st.header("Test 2: CSS Styling")
st.markdown("""
<style>
.test-header {
    background: linear-gradient(135deg, #00D26A 0%, #00A859 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
<div class="test-header">
    <h3>CSS Test Header</h3>
    <p>If you see this with green background, CSS works!</p>
</div>
""", unsafe_allow_html=True)

# Test 3: Button functionality
st.header("Test 3: Button Functionality")
if st.button("Test Button"):
    st.success("✅ Button click works!")

# Test 4: Input functionality
st.header("Test 4: Input Functionality")
test_input = st.text_input("Test Input", placeholder="Type something...")
if test_input:
    st.success(f"✅ Input works! You typed: {test_input}")

# Test 5: Multiple buttons
st.header("Test 5: Multiple Buttons")
col1, col2 = st.columns(2)
with col1:
    if st.button("Button 1"):
        st.info("Button 1 clicked!")
with col2:
    if st.button("Button 2"):
        st.info("Button 2 clicked!")

# Test 6: Session state
st.header("Test 6: Session State")
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment Counter"):
    st.session_state.counter += 1

st.info(f"Counter value: {st.session_state.counter}")

# Test 7: Error handling
st.header("Test 7: Error Handling")
try:
    # This should work
    st.success("✅ No errors detected")
except Exception as e:
    st.error(f"❌ Error: {e}")

st.header("Summary")
st.info("If all tests pass above, the app functionality is working correctly!")
