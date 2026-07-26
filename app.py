import sys
import os
import importlib.util

# Manually load the 'app/' package and register it in sys.modules
# to prevent the root 'app.py' filename from colliding with the 'app/' package folder.
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app')
init_file = os.path.join(app_dir, '__init__.py')

spec = importlib.util.spec_from_file_location('app', init_file)
app_module = importlib.util.module_from_spec(spec)
app_module.__path__ = [app_dir]
sys.modules['app'] = app_module
spec.loader.exec_module(app_module)

# Now we can safely use standard package imports!
import streamlit as st
from app.dashboard.views import (
    render_dashboard,
    render_create_ticket,
    render_inbox,
    render_predictions,
    render_analytics,
    render_settings
)
from app.services.database_service import init_db

# Page configuration
st.set_page_config(page_title="AI Helpdesk Automation Platform", page_icon="🎫", layout="wide")

def main():
    # Initialize the database
    init_db()
    
    # Sidebar navigation
    st.sidebar.title("🎫 AI Helpdesk")
    st.sidebar.markdown("Helpdesk Automation Platform v1.0.0")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Create Ticket", "Inbox", "Predictions", "Analytics", "Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by Scikit-Learn, SQLite & Streamlit")
    
    # Page Routing
    if page == "Dashboard":
        render_dashboard()
    elif page == "Create Ticket":
        render_create_ticket()
    elif page == "Inbox":
        render_inbox()
    elif page == "Predictions":
        render_predictions()
    elif page == "Analytics":
        render_analytics()
    elif page == "Settings":
        render_settings()

if __name__ == '__main__':
    main()
