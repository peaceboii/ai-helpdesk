import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ensure app/ is in sys.path when views are loaded
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.ticket import Ticket
from app.services.database_service import TicketRepository
from app.services.ticket_processor import TicketProcessor
from app.utils.config import load_config, save_config

processor = TicketProcessor()

def inject_responsive_css():
    """Injects premium, mobile-responsive custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
    /* Styling Streamlit Metrics into beautiful cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Dark Theme compatibility for Metrics */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] {
            background-color: #1e293b;
            border-color: #334155;
            color: #f8fafc;
        }
    }
    
    /* Responsive adjustments for mobile screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.5rem !important;
        }
        
        /* Stack column grids on tablet/mobile if they squish */
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 12px;
        }
    }
    
    /* Custom Badge/Status Styling */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    inject_responsive_css()
    st.header("📈 Helpdesk Overview")
    metrics = TicketRepository.get_dashboard_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Tickets", metrics['todays_tickets'])
    with col2:
        st.metric("Open Tickets", metrics['open_tickets'], delta_color="inverse")
    with col3:
        st.metric("Pending/Resolved", f"{metrics['pending_tickets']} / {metrics['resolved_tickets']}")
    with col4:
        st.metric("Average Confidence", f"{metrics['avg_confidence']:.1f}%")
        
    st.markdown("---")
    
    # Show recent activities
    st.subheader("🔔 Recent Ingested Tickets")
    tickets = TicketRepository.list_tickets(status="All")[:5]
    if tickets:
        for t in tickets:
            with st.expander(f"[{t.ticket_id}] - {t.subject} (From: {t.customer_name}) - Priority: {t.priority}"):
                st.write(f"**Source:** {t.source} | **Category:** {t.category} | **Assigned:** {t.assigned_team}")
                st.write(f"**Description:** {t.body[:200]}...")
    else:
        st.info("No tickets created yet. Use 'Create Ticket' or run the REST API to populate the database.")

def render_create_ticket():
    inject_responsive_css()
    st.header("✍️ Create Support Ticket")
    st.markdown("Submit a ticket manually. The AI processor will automatically extract entities, run sentiment analysis, clean text, classify categories, check duplicates, and assign teams.")
    
    with st.form("create_ticket_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name", placeholder="E.g. John Doe")
            email = st.text_input("Customer Email", placeholder="E.g. john@example.com")
        with col2:
            source = st.selectbox("Source Channel", ["Manual Entry", "Email", "WhatsApp", "Slack", "Telegram", "REST API"])
            subject = st.text_input("Subject", placeholder="Brief summary of the issue")
            
        body = st.text_area("Ticket Body / Details", placeholder="Enter full details here...")
        
        uploaded_file = st.file_uploader("Upload Attachment (PDF, Image)", type=["pdf", "png", "jpg", "jpeg"])
        
        submitted = st.form_submit_button("Ingest & Process Ticket", type="primary")
        
        if submitted:
            if not customer_name or not email or (not subject and not body):
                st.error("Please fill in the required fields (Name, Email, and Subject/Body).")
            else:
                att_name = None
                att_data = None
                if uploaded_file is not None:
                    att_name = uploaded_file.name
                    att_data = uploaded_file.read()
                    
                # Create raw Ticket
                ticket_id = TicketRepository.get_next_ticket_id()
                new_ticket = Ticket(
                    ticket_id=ticket_id,
                    customer_name=customer_name,
                    email=email,
                    source=source,
                    subject=subject,
                    body=body,
                    attachment_name=att_name,
                    attachment_data=att_data
                )
                
                with st.spinner("Processing ticket..."):
                    res = processor.process(new_ticket)
                    
                if res.get("status") == "Rejected":
                    st.error(f"Ticket Rejected: {res.get('reason')}")
                elif res.get("status") == "Spam":
                    st.warning("⚠️ Ticket classified as SPAM and discarded.")
                else:
                    st.success(f"🎉 Ticket processed successfully! ID: {res.get('ticket_id')}")
                    
                    # Display Results
                    st.markdown("### Processed Results")
                    col_res1, col_res2, col_res3 = st.columns(3)
                    with col_res1:
                        st.info(f"**Category:** {res.get('category')}")
                        st.info(f"**Confidence:** {res.get('confidence'):.1f}%")
                    with col_res2:
                        st.info(f"**Priority:** {res.get('priority')}")
                        st.info(f"**Sentiment:** {res.get('sentiment')}")
                    with col_res3:
                        st.info(f"**Assigned:** {res.get('assigned_team')}")
                        if res.get("is_duplicate"):
                            st.warning(f"⚠️ Duplicate of: {res.get('duplicate_of')}")
                            
                    st.text_area("Generated Auto-Response", value=res.get("auto_response"), height=200, disabled=True)

def render_inbox():
    inject_responsive_css()
    st.header("📥 Helpdesk Inbox")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search = st.text_input("Search", placeholder="ID, name, subject, body...")
    with col2:
        category_filter = st.selectbox("Category Filter", ["All", "Billing", "Technical", "HR", "General", "Needs Human Review"])
    with col3:
        priority_filter = st.selectbox("Priority Filter", ["All", "HIGH", "NORMAL"])
    with col4:
        status_filter = st.selectbox("Status Filter", ["All", "Open", "Pending", "Resolved", "Spam"])
        
    tickets = TicketRepository.list_tickets(search=search, category=category_filter, priority=priority_filter, status=status_filter)
    
    if not tickets:
        st.info("No tickets match the active filters.")
        return
        
    # Convert list of tickets to pandas dataframe for clean rendering
    data = []
    for t in tickets:
        data.append({
            "ID": t.ticket_id,
            "Customer": t.customer_name,
            "Source": t.source,
            "Category": t.category,
            "Priority": t.priority,
            "Status": t.status,
            "Confidence": f"{t.confidence:.1f}%",
            "Date": t.created_time
        })
    df = pd.DataFrame(data)
    
    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Manage/View details
    st.markdown("### 🔍 Ticket Detail Examiner")
    selected_id = st.selectbox("Select Ticket ID to View/Modify", [t.ticket_id for t in tickets])
    
    if selected_id:
        t = TicketRepository.get_ticket(selected_id)
        if t:
            col_det1, col_det2 = st.columns([2, 1])
            with col_det1:
                st.markdown(f"#### **Subject: {t.subject}**")
                st.caption(f"Created: {t.created_time} | Channel: {t.source} | Email: {t.email}")
                st.markdown("**Description:**")
                st.info(t.body)
                
                # Show attachments
                if t.attachment_name:
                    st.markdown(f"📎 **Attachment:** `{t.attachment_name}`")
                    
                # Show entities
                if t.entities:
                    st.markdown("**Extracted Entities:**")
                    ent_cols = st.columns(len(t.entities))
                    for idx, (k, v) in enumerate(t.entities.items()):
                        with ent_cols[idx % len(ent_cols)]:
                            st.metric(k, v)
                            
                # Show merge duplicate option
                if t.merged_with:
                    st.warning(f"⚠️ This ticket has been marked as a possible duplicate of **{t.merged_with}**.")
                    if st.button("Merge and Resolve Ticket", type="secondary"):
                        t.status = "Resolved"
                        TicketRepository.update_ticket(t)
                        st.success(f"Ticket {t.ticket_id} merged with {t.merged_with} and status set to Resolved.")
                        st.rerun()
            with col_det2:
                st.markdown("#### **Control Center**")
                
                # Status modification
                new_status = st.selectbox("Update Status", ["Open", "Pending", "Resolved", "Spam"], index=["Open", "Pending", "Resolved", "Spam"].index(t.status))
                if new_status != t.status:
                    TicketRepository.update_ticket_status(t.ticket_id, new_status)
                    st.success("Status updated!")
                    st.rerun()
                    
                st.markdown(f"**Classification Confidence:** `{t.confidence:.1f}%`")
                st.markdown(f"**Priority:** `{t.priority}`")
                st.markdown(f"**Sentiment:** `{t.sentiment}`")
                st.markdown(f"**Assigned Department:** `{t.assigned_team}`")
                
                # Activity log
                st.markdown("**History Log:**")
                logs = TicketRepository.get_activity_logs(t.ticket_id)
                for log in logs:
                    st.caption(f"[{log['timestamp']}] {log['action']} - {log['details']}")

def render_predictions():
    inject_responsive_css()
    # Legacy Classifier Sandbox Interface
    st.header("🎯 Sandbox AI Ticket Classifier")
    st.markdown("Test the underlying Scikit-Learn Logistic Regression / Naive Bayes model in sandbox mode.")
    
    # Import legacy predict method to preserve exact logic
    from predict import predict_ticket
    
    subject = st.text_input("Sandbox Subject", placeholder="E.g., Server is down")
    body = st.text_area("Sandbox Body", placeholder="E.g., Production DB connection keeps timing out...")
    
    if st.button("Run Sandbox Prediction", type="primary"):
        if not subject and not body:
            st.warning("Please fill in details.")
        else:
            with st.spinner("Classifying..."):
                res = predict_ticket(subject, body)
                
            col1, col2, col3 = st.columns(3)
            with col1:
                category = res['Predicted Category']
                if category == "Needs Human Review":
                    st.error(f"### ⚠️ {category}")
                else:
                    st.success(f"### 🎯 {category}")
            with col2:
                st.metric("Confidence Score", f"{res['Confidence %']:.2f}%")
            with col3:
                priority = res['Priority']
                if priority == "HIGH":
                    st.error(f"### 🚨 {priority}")
                else:
                    st.info(f"### 🟢 {priority}")
                    
            st.markdown("---")
            st.subheader("Class Probability Visualization")
            prob_df = pd.DataFrame(
                list(res['Probabilities'].items()),
                columns=['Category', 'Probability (%)']
            )
            prob_df.set_index('Category', inplace=True)
            st.bar_chart(prob_df)

def render_analytics():
    inject_responsive_css()
    st.header("📊 Performance & Distribution Analytics")
    
    tickets = TicketRepository.list_tickets(status="All")
    if not tickets:
        st.info("No data available for analytics yet.")
        return
        
    df = pd.DataFrame([{
        "category": t.category,
        "source": t.source,
        "priority": t.priority,
        "sentiment": t.sentiment,
        "status": t.status,
        "confidence": t.confidence,
        "date": t.created_time.split(" ")[0]
    } for t in tickets])
    
    # 2x2 grid of plots
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tickets per Category")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='category', palette='Blues_r', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close()
        
        st.subheader("Tickets per Ingestion Source")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='source', palette='Greens_r', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close()
        
    with col2:
        st.subheader("Sentiment Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.countplot(data=df, x='sentiment', palette='Oranges_r', ax=ax)
        st.pyplot(fig)
        plt.close()
        
        st.subheader("Confidence Score Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(data=df, x='confidence', kde=True, color='purple', bins=10, ax=ax)
        st.pyplot(fig)
        plt.close()

def render_settings():
    inject_responsive_css()
    st.header("⚙️ Platform Settings")
    config = load_config()
    
    # Routing Rules
    st.subheader("Routing Engine Mappings")
    routing_rules = config.get("routing_rules", {})
    updated_routing = {}
    for cat, team in routing_rules.items():
        updated_routing[cat] = st.text_input(f"Category: {cat} maps to", value=team)
        
    # Thresholds
    st.markdown("---")
    st.subheader("Confidence Threshold")
    confidence_threshold = st.slider("Human Review Fallback Threshold (%)", min_value=0.0, max_value=100.0, value=float(config.get("confidence_threshold", 60.0)))
    
    # Spam words
    st.markdown("---")
    st.subheader("Spam keywords")
    spam_keywords = st.text_area("List keywords (comma-separated)", value=", ".join(config.get("spam_keywords", [])))
    
    if st.button("Save Platform Configurations", type="primary"):
        # Compile config
        config["routing_rules"] = updated_routing
        config["confidence_threshold"] = confidence_threshold
        config["spam_keywords"] = [s.strip() for s in spam_keywords.split(",") if s.strip()]
        save_config(config)
        st.success("Configurations saved successfully!")
