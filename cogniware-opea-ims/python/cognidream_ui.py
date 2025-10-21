"""
Streamlit UI for CogniDream admin interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from cognidream_api import CogniDreamAPI, UserSession, SystemMetrics, ModelStats, UserStats

# Initialize session state
if 'api' not in st.session_state:
    st.session_state.api = CogniDreamAPI()

# Page config
st.set_page_config(
    page_title="CogniDream Admin",
    page_icon="🧠",
    layout="wide"
)

# Sidebar
st.sidebar.title("CogniDream Admin")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Sessions", "Models", "Users", "Settings"]
)

# Helper functions
def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def create_gauge_chart(value: float, title: str, min_val: float = 0, max_val: float = 100) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_val/3], 'color': "lightgray"},
                {'range': [max_val/3, 2*max_val/3], 'color': "gray"},
                {'range': [2*max_val/3, max_val], 'color': "darkgray"}
            ]
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# Dashboard page
if page == "Dashboard":
    st.title("System Dashboard")
    
    # Auto-refresh
    if st.checkbox("Auto-refresh", value=True):
        time.sleep(1)  # Wait for 1 second before refreshing
    
    # Get system metrics
    metrics = st.session_state.api.get_system_metrics()
    
    # Create metrics columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.plotly_chart(create_gauge_chart(
            metrics.vram_usage,
            "VRAM Usage (%)",
            max_val=100
        ))
    
    with col2:
        st.plotly_chart(create_gauge_chart(
            metrics.avg_latency,
            "Average Latency (ms)",
            max_val=1000
        ))
    
    with col3:
        st.plotly_chart(create_gauge_chart(
            metrics.active_sessions,
            "Active Sessions",
            max_val=100
        ))
    
    # GPU utilization chart
    st.subheader("GPU Utilization")
    gpu_data = pd.DataFrame({
        'GPU': [f"GPU {i}" for i in range(len(metrics.gpu_utilization))],
        'Utilization': metrics.gpu_utilization
    })
    fig = px.bar(gpu_data, x='GPU', y='Utilization',
                 title='GPU Utilization by Device',
                 labels={'Utilization': 'Utilization (%)'})
    st.plotly_chart(fig, use_container_width=True)
    
    # System statistics
    st.subheader("System Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Requests", metrics.total_requests)
    with col2:
        st.metric("Total Tokens", metrics.total_tokens)
    with col3:
        st.metric("Active Sessions", metrics.active_sessions)
    with col4:
        st.metric("Average Latency", f"{metrics.avg_latency:.2f} ms")

# Sessions page
elif page == "Sessions":
    st.title("Session Management")
    
    # Create new session
    with st.expander("Create New Session"):
        with st.form("create_session"):
            user_id = st.text_input("User ID")
            model_id = st.text_input("Model ID")
            if st.form_submit_button("Create Session"):
                try:
                    session = st.session_state.api.create_session(user_id, model_id)
                    st.success(f"Session created: {session.session_id}")
                except Exception as e:
                    st.error(f"Failed to create session: {str(e)}")
    
    # Active sessions
    st.subheader("Active Sessions")
    sessions = st.session_state.api.get_active_sessions()
    
    if sessions:
        # Convert sessions to DataFrame
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'Session ID': session.session_id,
                'User ID': session.user_id,
                'Model ID': session.model_id,
                'Created At': format_datetime(session.created_at),
                'Last Activity': format_datetime(session.last_activity),
                'Requests': session.requests_processed,
                'Tokens': session.tokens_generated
            })
        
        df = pd.DataFrame(sessions_data)
        st.dataframe(df)
        
        # Session actions
        session_id = st.selectbox("Select Session", [s.session_id for s in sessions])
        if st.button("End Session"):
            if st.session_state.api.end_session(session_id):
                st.success("Session ended successfully")
                st.experimental_rerun()
            else:
                st.error("Failed to end session")
    else:
        st.info("No active sessions")

# Models page
elif page == "Models":
    st.title("Model Management")
    
    # Model selection
    model_id = st.text_input("Model ID")
    
    if model_id:
        # Get model stats
        stats = st.session_state.api.get_model_stats(model_id)
        
        if stats:
            # Model statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Requests Processed", stats.requests_processed)
            with col2:
                st.metric("Tokens Generated", stats.tokens_generated)
            with col3:
                st.metric("Average Latency", f"{stats.avg_latency:.2f} ms")
            
            # Resource usage
            st.subheader("Resource Usage")
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_gauge_chart(
                    stats.vram_usage,
                    "VRAM Usage (%)",
                    max_val=100
                ))
            with col2:
                st.plotly_chart(create_gauge_chart(
                    stats.gpu_utilization,
                    "GPU Utilization (%)",
                    max_val=100
                ))
            
            # Model configuration
            st.subheader("Model Configuration")
            with st.form("update_config"):
                max_tokens = st.number_input("Max Tokens", value=2048, min_value=1)
                temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
                top_p = st.slider("Top P", 0.0, 1.0, 0.9)
                
                if st.form_submit_button("Update Configuration"):
                    config = {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p
                    }
                    if st.session_state.api.update_model_config(model_id, config):
                        st.success("Configuration updated successfully")
                    else:
                        st.error("Failed to update configuration")
        else:
            st.error("Model not found")

# Users page
elif page == "Users":
    st.title("User Management")
    
    # User selection
    user_id = st.text_input("User ID")
    
    if user_id:
        # Get user stats
        stats = st.session_state.api.get_user_stats(user_id)
        
        if stats:
            # User statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requests", stats.total_requests)
            with col2:
                st.metric("Total Tokens", stats.total_tokens)
            with col3:
                st.metric("Active Sessions", stats.active_sessions)
            with col4:
                st.metric("Average Latency", f"{stats.avg_latency:.2f} ms")
            
            # User sessions
            st.subheader("User Sessions")
            sessions = st.session_state.api.get_active_sessions()
            user_sessions = [s for s in sessions if s.user_id == user_id]
            
            if user_sessions:
                sessions_data = []
                for session in user_sessions:
                    sessions_data.append({
                        'Session ID': session.session_id,
                        'Model ID': session.model_id,
                        'Created At': format_datetime(session.created_at),
                        'Last Activity': format_datetime(session.last_activity),
                        'Requests': session.requests_processed,
                        'Tokens': session.tokens_generated
                    })
                
                df = pd.DataFrame(sessions_data)
                st.dataframe(df)
            else:
                st.info("No active sessions for this user")
        else:
            st.error("User not found")

# Settings page
elif page == "Settings":
    st.title("Settings")
    
    # API configuration
    st.subheader("API Configuration")
    base_url = st.text_input("API Base URL", value=st.session_state.api.base_url)
    if st.button("Update API URL"):
        st.session_state.api = CogniDreamAPI(base_url)
        st.success("API URL updated successfully")
    
    # Theme settings
    st.subheader("Theme Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # About
    st.subheader("About")
    st.markdown("""
    ### CogniDream Admin Interface
    Version: 1.0.0
    
    A modern web interface for managing CogniDream LLM instances.
    """) 