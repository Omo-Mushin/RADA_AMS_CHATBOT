"""
Custom UI components for professional chat interface
"""

import streamlit as st
from datetime import datetime
import json
import os

def apply_custom_css():
    """Apply custom CSS for professional WhatsApp-like interface"""
    st.markdown("""
    <style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 20px auto;
        max-width: 900px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        min-height: 70vh;
    }
    
    /* Message bubbles */
    .user-message {
        background: #DCF8C6;
        color: #000;
        padding: 12px 16px;
        border-radius: 18px 18px 5px 18px;
        margin: 10px 0;
        max-width: 70%;
        margin-left: auto;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        animation: slideInRight 0.3s ease;
    }
    
    .assistant-message {
        background: #FFFFFF;
        color: #000;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 5px;
        margin: 10px 0;
        max-width: 70%;
        margin-right: auto;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #E5E5EA;
        animation: slideInLeft 0.3s ease;
    }
    
    /* Timestamps */
    .timestamp {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
        text-align: right;
    }
    
    /* Input box */
    .stChatInput {
        border-radius: 25px;
        border: 2px solid #667eea;
        padding: 10px 20px;
    }
    
    /* Animations */
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Header */
    .chat-header {
        background: #075E54;
        color: white;
        padding: 15px 20px;
        border-radius: 15px 15px 0 0;
        margin: -20px -20px 20px -20px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .chat-header h1 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
    }
    
    .status-indicator {
        width: 10px;
        height: 10px;
        background: #4CAF50;
        border-radius: 50%;
        margin-left: 10px;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 20px;
        background: #667eea;
        color: white;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #5568d3;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Tables in messages */
    .assistant-message table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    
    .assistant-message th {
        background: #667eea;
        color: white;
        padding: 8px;
        text-align: left;
    }
    
    .assistant-message td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 10px;
    }
    
    .typing-indicator span {
        height: 10px;
        width: 10px;
        background: #999;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
    </style>
    """, unsafe_allow_html=True)

def render_chat_header(db_source="cloud"):
    """Render professional chat header"""
    status_color = "#4CAF50" if db_source else "#FFC107"
    
    st.markdown(f"""
    <div class="chat-header">
        <div style="display: flex; align-items: center; width: 100%;">
            <div style="width: 45px; height: 45px; background: white; border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                <span style="font-size: 24px;">🧠</span>
            </div>
            <div style="flex: 1;">
                <h1 style="margin: 0; font-size: 20px;">RADA AMS Assistant</h1>
                <p style="margin: 0; font-size: 12px; opacity: 0.8;">
                    Production Intelligence • {db_source.capitalize()} Database
                </p>
            </div>
            <div style="width: 10px; height: 10px; background: {status_color}; 
                        border-radius: 50%; animation: pulse 2s infinite;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_message(role, content, timestamp=None):
    """Render a chat message bubble"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    
    message_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="{message_class}">
        <div style="display: flex; align-items: start;">
            <span style="font-size: 16px; margin-right: 8px;">{icon}</span>
            <div style="flex: 1;">
                <div>{content}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_typing_indicator():
    """Show typing indicator while processing"""
    st.markdown("""
    <div class="assistant-message">
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render professional sidebar with controls"""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Download chat history
        if st.session_state.get('messages'):
            chat_json = json.dumps(st.session_state.messages, indent=2)
            st.download_button(
                label="📥 Download Chat History",
                data=chat_json,
                file_name=f"rada_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Quick tips
        st.markdown("### 💡 Quick Tips")
        st.markdown("""
        **Sample Questions:**
        
        📊 **Production Queries**
        - "What is the oil production for Awoba flowstation?"
        - "Show me top 5 wells by gas production"
        - "Total water production for OML 24"
        
        📅 **Date-Based**
        - "Production data for September 2025"
        - "Compare Awoba vs Ekulama in October"
        
        🔍 **Well-Specific**
        - "Give me wells in Ekulama 1"
        - "Performance of AWOB008T well"
        
        📈 **Analytics**
        - "Average BSW for October 2025"
        - "Highest producing well in OML 24"
        """)
        
        st.markdown("---")
        
        # System info
        with st.expander("ℹ️ System Information"):
            st.markdown(f"""
            **Version:** 1.0.0  
            **Database:** ChromaDB  
            **LLM:** Groq Llama 3.3 70B  
            **Last Updated:** {datetime.now().strftime("%Y-%m-%d")}
            """)
        
        # Feedback
        st.markdown("---")
        st.markdown("### 📬 Feedback")
        feedback = st.text_area("Share your feedback:", placeholder="Your feedback helps us improve...")
        if st.button("Submit Feedback", use_container_width=True):
            if feedback:
                # Save feedback to file
                save_feedback(feedback)
                st.success("✅ Thank you for your feedback!")
            else:
                st.warning("Please enter some feedback first")

def save_feedback(feedback):
    """Save user feedback to file"""
    feedback_file = "feedback.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Feedback: {feedback}\n")

def show_example_queries():
    """Show clickable example queries"""
    st.markdown("### 🎯 Try These Questions")
    
    examples = [
        "How many wells are in Awoba flowstation?",
        "What is the highest producing well?",
        "Show me production for October 2025",
        "Compare Awoba and Ekulama 1"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                return example
    
    return None
