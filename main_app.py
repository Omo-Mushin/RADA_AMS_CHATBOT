"""
RADA AMS Assistant - Main Streamlit Application
Professional petroleum engineering chatbot interface
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import custom modules
from database import get_vector_db
from chatbot_engine import (
    load_embedding_model,
    load_reranker,
    init_groq_client,
    query_chatbot
)
from ui_components import (
    apply_custom_css,
    render_chat_header,
    render_message,
    render_typing_indicator,
    render_sidebar,
    show_example_queries
)

# Page configuration
st.set_page_config(
    page_title="🧠 RADA AMS Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "initialized" not in st.session_state:
    st.session_state.initialized = False

@st.cache_resource
def initialize_app():
    """Initialize all components - cached for performance"""
    try:
        # Load vector database
        collection, db_source = get_vector_db()
        
        # Load models
        embedding_model = load_embedding_model()
        reranker = load_reranker()
        groq_client = init_groq_client()
        
        return {
            "collection": collection,
            "embedding_model": embedding_model,
            "reranker": reranker,
            "groq_client": groq_client,
            "db_source": db_source,
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def process_query(user_input, components):
    """Process user query and return response"""
    try:
        response = query_chatbot(
            collection=components["collection"],
            embedding_model=components["embedding_model"],
            reranker=components["reranker"],
            groq_client=components["groq_client"],
            user_question=user_input,
            debug=False
        )
        return response
    except Exception as e:
        return f"⚠️ Error processing query: {str(e)}"

def main():
    """Main application flow"""
    
    # Apply custom styling
    apply_custom_css()
    
    # Initialize components
    with st.spinner("🔄 Initializing RADA AMS Assistant..."):
        components = initialize_app()
    
    # Check initialization status
    if components["status"] == "error":
        st.error(f"❌ Failed to initialize: {components['error']}")
        st.stop()
    
    st.session_state.initialized = True
    
    # Render chat header
    render_chat_header(db_source=components.get("db_source", "unknown"))
    
    # Render sidebar
    render_sidebar()
    
    # Welcome message for new users
    if not st.session_state.messages:
        with st.container():
            st.markdown("""
            <div style="background: #f0f7ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #1976d2;">👋 Welcome to RADA AMS Assistant!</h3>
                <p style="margin: 0; color: #555;">
                    I'm your AI-powered petroleum engineering assistant. Ask me about:
                </p>
                <ul style="margin: 10px 0; color: #555;">
                    <li>📊 Production data and statistics</li>
                    <li>🛢️ Well performance and flowstations</li>
                    <li>📈 Production trends and comparisons</li>
                    <li>📅 Date-specific production queries</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Show example queries
        example_clicked = show_example_queries()
        if example_clicked:
            # Simulate user input
            st.session_state.example_query = example_clicked
            st.rerun()
    
    # Handle example query from button click
    if hasattr(st.session_state, 'example_query'):
        user_input = st.session_state.example_query
        del st.session_state.example_query
        
        # Add to messages
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Process query
        with st.spinner():
            response = process_query(user_input, components)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        st.rerun()
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for msg in st.session_state.messages:
            render_message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp", datetime.now().strftime("%H:%M"))
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your question here... 💬")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Show typing indicator
        with st.spinner("🤔 Analyzing data..."):
            response = process_query(user_input, components)
        
        # Add assistant response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Rerun to display new messages
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; padding: 20px 0;">
        <p>🔒 Secure • 🚀 Powered by Groq & ChromaDB • 💡 Built with Streamlit</p>
        <p style="margin: 5px 0;">© 2024 RADA AMS. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
