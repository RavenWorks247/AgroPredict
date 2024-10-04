import streamlit as st
import requests
import json
import datetime
import os
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase
import re
from dotenv import load_dotenv
load_dotenv()

# Initialize Firebase Admin SDK
cred = credentials.ApplicationDefault()
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

# Configure Firebase for authentication
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
}
firebase = pyrebase.initialize_app(firebase_config)
auth_firebase = firebase.auth()

# Cloud Run service URL
GEMINI_SERVICE_URL = os.getenv('APPURL')

# Set page config
st.set_page_config(page_title="AgroPredict", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://i.postimg.cc/bNpkyW4Y/3065775.jpg");
        background-attachment: fixed;
        background-size: cover;
        background-color: rgba(255, 255, 255, 0.7);
        background-blend-mode: overlay;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: -1;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .chat-message {
        display: flex;
        margin-bottom: 10px;
    }
    .user-message {
        justify-content: flex-end;
    }
    .assistant-message {
        justify-content: flex-start;
    }
    .message-content {
        max-width: 70%;
        padding: 10px;
        border-radius: 10px;
    }
    .user-message .message-content {
        background-color: #DCF8C6;
    }
    .assistant-message .message-content {
        background-color: #E8E8E8;
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication functions
def sign_up():
    email = st.text_input("Email address", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    
    # Add instruction text for password rules
    st.markdown(
        "<p style='font-size: 13px; color: #555555;'>Password must be at least 8 characters long and contain at least one letter and one number.</p>",
        unsafe_allow_html=True
    )
    
    if st.button("Sign Up", key="signup_button"):
        # Enforce minimum password length of 8 characters
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return
        
        # Enforce basic password rules: at least one letter and one number
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            st.error("Password must contain at least one letter and one number.")
            return

        try:
            # Create the user
            auth_firebase.create_user_with_email_and_password(email, password)
            
            # Automatically log in the user after successful signup
            user = auth_firebase.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.session_state.authenticated = True
            st.success("Account created and logged in successfully!")
            st.rerun()
        
        except Exception as e:
            # Custom error message for weak password or other errors
            if "WEAK_PASSWORD" in str(e):
                st.error("WEAK PASSWORD. Password must have 8 characters or more and contain both letters and numbers.")
            else:
                st.error(f"Error: {str(e)}")

def login():
    email = st.text_input("Email address", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login", key="login_button"):
        try:
            user = auth_firebase.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
            st.rerun()
        
        except Exception as e:
            # Extract error message and display more readable messages
            error_message = str(e)

            if "INVALID_EMAIL" in error_message:
                st.error("The email address is invalid. Please check your email format.")
            elif "EMAIL_NOT_FOUND" in error_message:
                st.error("No account found with this email. Please sign up first.")
            elif "INVALID_PASSWORD" in error_message:
                st.error("The password is incorrect. Please try again.")
            elif "INVALID_LOGIN_CREDENTIALS" in error_message:
                st.error("Invalid login credentials. Please check your email and password.")
            elif "USER_DISABLED" in error_message:
                st.error("This account has been disabled. Please contact support.")
            else:
                st.error("An unexpected error occurred. Please try again later.")

def logout():
    st.session_state.user = None
    st.session_state.authenticated = False
    st.success("Logged out successfully!")
    st.rerun()

# Crop analysis functions
def analyze_crop_suitability(sentence, session_id, user_id):
    url = f"{GEMINI_SERVICE_URL}/analyze"
    payload = {"sentence": sentence, "session_id": session_id, "user_id": user_id}
    response = requests.post(url, json=payload)
    
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        st.error(f"Error occurred: {err}")
    except json.JSONDecodeError:
        st.error("Failed to parse the response from the server.")
    return None

def chat_with_bot(message, session_id, user_id):
    url = f"{GEMINI_SERVICE_URL}/chat"
    payload = {"message": message, "session_id": session_id, "user_id": user_id}
    response = requests.post(url, json=payload)
    
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        st.error(f"Error occurred: {err}")
    except json.JSONDecodeError:
        st.error("Failed to parse the response from the server.")
    return None

def save_session_to_storage(user_id, session_id, analysis_input, analysis_result, chat_messages=None):
    if chat_messages is None:
        chat_messages = []

    # Ensure session_id and user_id are provided
    if not session_id or not user_id:
        raise ValueError("session_id and user_id must be provided")
    
    url = f"{GEMINI_SERVICE_URL}/save_session"
    session_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "analysis_input": analysis_input,
        "analysis_result": analysis_result,
        "chat_messages": chat_messages
    }
    payload = {"user_id": user_id, "session_id": session_id, "session_data": session_data}
    response = requests.post(url, json=payload)
    
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        st.error(f"Error occurred: {err}")
    return None

# Main application functions
def list_saved_sessions(user_id):
    url = f"{GEMINI_SERVICE_URL}/list_sessions"
    params = {"user_id": user_id}
    response = requests.get(url, params=params)
    
    try:
        response.raise_for_status()
        sessions = response.json()
        return sorted([(session_id, created_time) for session_id, created_time in sessions.items()], 
                     key=lambda x: x[1], reverse=True)
    except Exception as e:
        st.error(f"Error loading sessions: {str(e)}")
        return []

def load_session(user_id, session_id):
    url = f"{GEMINI_SERVICE_URL}/load_session"
    params = {"user_id": user_id, "session_id": session_id}
    response = requests.get(url, params=params)
    
    try:
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return None

def start_new_chat(user_id):
    if hasattr(st.session_state, 'session_id'):
        save_session_to_storage(
            user_id,
            st.session_state.session_id,
            st.session_state.analysis_input,
            st.session_state.analysis_result,
            st.session_state.chat_messages,
        )
    
    new_session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.session_id = new_session_id
    st.session_state.analysis_input = ""
    st.session_state.analysis_result = None
    st.session_state.chat_messages = []
    st.rerun()

def display_user_profile():
    if 'show_profile' not in st.session_state:
        st.session_state.show_profile = False
    
    # Use a button with the same position as the icon to toggle the profile
    if st.button("User Profile", key="profile_button"):
        st.session_state.show_profile = not st.session_state.show_profile
    
    if st.session_state.show_profile:
        with st.sidebar:
            st.subheader("User Profile")
            st.write(f"Email: {st.session_state.user['email']}")
            if st.button("Logout"):
                logout()

def main_app():
    user_id = st.session_state.user['localId']
    display_user_profile()

    # Sidebar
    with st.sidebar:
        if st.button("Start New Chat", key="new_chat_sidebar"):
            start_new_chat(user_id)
        
        st.subheader("Saved Contexts")
        saved_sessions = list_saved_sessions(user_id)
        for session_id, timestamp in saved_sessions:
            if st.button(f"{timestamp[:10]} - {session_id}", key=f"session_{session_id}"):
                loaded_session = load_session(user_id, session_id)
                if loaded_session:
                    st.session_state.session_id = session_id
                    st.session_state.analysis_input = loaded_session.get("analysis_input", "")
                    st.session_state.analysis_result = loaded_session.get("analysis_result", None)
                    st.session_state.chat_messages = loaded_session.get("chat_messages", [])
                    st.rerun()

    # Main content area
    st.title("AgroPredict")
    
    # Initialize session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if "analysis_input" not in st.session_state:
        st.session_state.analysis_input = ""
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Analysis input
    analysis_input = st.text_area("Enter your crop, region and growing season for tailored agricultural advice:", 
                                 value=st.session_state.analysis_input, height=100)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Analyze"):
            if analysis_input:
                with st.spinner("Analyzing..."):
                    result = analyze_crop_suitability(analysis_input, st.session_state.session_id, user_id)
                if result:
                    st.session_state.analysis_input = analysis_input
                    st.session_state.analysis_result = result
                    st.session_state.chat_messages = []
                    save_session_to_storage(
                        user_id,
                        st.session_state.session_id,
                        st.session_state.analysis_input,
                        st.session_state.analysis_result,
                        st.session_state.chat_messages,
                    )
                    st.rerun()
            else:
                st.warning("Please enter a description for analysis.")

    # Display Analysis Result and Chat
    if st.session_state.analysis_result:
        st.subheader("Analysis Result:")
        analysis_text = st.session_state.analysis_result.get('crop_analysis', '')
        st.markdown(analysis_text)

        st.subheader("Chat about the Analysis")
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask a question about the analysis:"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Thinking..."):
                response = chat_with_bot(prompt, st.session_state.session_id, user_id)
            if response:
                st.session_state.chat_messages.append({"role": "assistant", "content": response["response"]})
            
            save_session_to_storage(
                user_id,
                st.session_state.session_id,
                st.session_state.analysis_input,
                st.session_state.analysis_result,
                st.session_state.chat_messages   
            )
            
            st.rerun()

def auth_page():
    st.title("Welcome to AgroPredict")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        login()
    
    with tab2:
        sign_up()

# Main execution
if __name__ == "__main__":
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        auth_page()
    else:
        main_app()