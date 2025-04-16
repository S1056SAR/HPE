import streamlit as st
import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
retry_strategy = Retry(
    total=5,
    backoff_factor=2,  
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST"]  
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)

st.set_page_config(
    page_title="Network Interoperatability assistant",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main container */
    .main {
        background-color: #f8f9fa;
        padding: 2rem;
    }
    
    /* Header styling */
    .stTitle {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        padding-bottom: 2rem;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        position: relative;
        font-size: 16px;
        line-height: 1.6;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: 60px;
        margin-right: 20px;
    }
    
    .assistant-message {
        background-color: #f1f3f4;
        color: #2c3e50;
        margin-left: 20px;
        margin-right: 60px;
    }
    
    /* Avatar styling */
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        position: absolute;
        bottom: 0;
    }
    
    .user-avatar {
        right: -50px;
        background-color: #007bff;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }
    
    .assistant-avatar {
        left: -50px;
        background-color: #e91e63;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        background-color: white;
        padding: 15px;
        font-size: 16px;
        border-radius: 25px;
        border: 2px solid #e1e4e8;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
    }
    
    /* Analysis expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f1f3f4;
    }
    
    /* Remove white bar under title */
    .stMarkdown {
        margin-bottom: 0 !important;
    }
    
    /* Custom title container */
    .title-container {
        background: linear-gradient(90deg, #0056b3 0%, #007bff 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .title-text {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    
    /* Remove default streamlit margins */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://www.arubanetworks.com/wp-content/themes/Aruba2015/images/hpe-aruba-networking-logo_1200x627.png", width=200)
    st.markdown("### About")
    st.markdown("""
    This AI assistant helps you with:
    - Product specifications
    - Technical Specifications
    - Configuration Guidelines
    - Troubleshooting Help
    """)
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Replace the title section with this custom HTML
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🌐 Network Interoperability Assistant</h1>
    </div>
""", unsafe_allow_html=True)

# Chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    is_user = message["role"] == "user"
    avatar_letter = "U" if is_user else "A"
    
    message_html = f"""
        <div class="chat-message {'user-message' if is_user else 'assistant-message'}">
            {message['content']}
            <div class="avatar {'user-avatar' if is_user else 'assistant-avatar'}">
                {avatar_letter}
            </div>
        </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

if prompt := st.chat_input("💭 Ask me anything..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Processing your question...'):
        try:
            response = http.post(
                "http://localhost:8000/query",
                json={"query": prompt},
                timeout=180  
            )
            response.raise_for_status()
            
            # Extract response data
            data = response.json()
            answer = data.get("response", "No response available")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            if "analysis" in data:
                with st.expander("Analysis Details"):
                    st.json(data["analysis"])
            
            # Rerun to update the display
            st.rerun()
            
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out after 3 minutes. Try breaking your question into smaller parts.")
            st.info("💡 Tip: More specific questions tend to process faster.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Connection failed. Please verify that the API server (main.py) is running.")
            st.info("Run 'python main.py' in a separate terminal to start the API server.")
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error: {str(e)}")
            st.info("Please check if the API server is running and try again.")
        except KeyError as e:
            st.error(f"❌ Unexpected response format: {str(e)}")
            st.json(response.json())  # Display the raw response for debugging

# Footer
st.markdown("---")
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>Built using Streamlit</small>
        </div>
        """, unsafe_allow_html=True)