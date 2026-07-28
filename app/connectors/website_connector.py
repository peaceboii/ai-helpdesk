from typing import Dict, Any, Optional
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class WebsiteConnector(BaseConnector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses Website Contact Form payload.
        Expected keys: name, email, phone, department, subject, description
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        name = payload.get("name", "Website Visitor")
        email = payload.get("email", "visitor@example.com")
        phone = payload.get("phone", "")
        department = payload.get("department", "General")
        subject = payload.get("subject", "Website Contact Form Submission")
        description = payload.get("description", "")
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=name,
            email=email,
            source="Website Contact Form",
            subject=subject,
            body=description,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
        
        # Populate routing and context fields
        ticket.entities["Phone"] = phone
        ticket.entities["Department Option"] = department
        
        return ticket

    def get_embed_code(self, base_url: str) -> str:
        """
        Generates embeddable JS snippet with standard premium styling.
        """
        escaped_base_url = base_url.rstrip('/')
        return f"""<!-- AI Helpdesk Contact Form Embed -->
<div id="ai-helpdesk-form-container"></div>
<script>
(function() {{
    const container = document.getElementById('ai-helpdesk-form-container');
    if (!container) return;
    
    container.innerHTML = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 550px; margin: 20px auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05); background: #ffffff; box-sizing: border-box;">
            <h3 style="margin-top: 0; margin-bottom: 8px; color: #0f172a; font-size: 1.5rem; font-weight: 700;">Submit a Support Request</h3>
            <p style="margin-top: 0; margin-bottom: 24px; color: #64748b; font-size: 0.875rem;">Fill out the details below. Our AI categorizer will route your ticket immediately.</p>
            <form id="ai-helpdesk-contact-form">
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Full Name</label>
                    <input type="text" name="name" required style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; outline: none; transition: border-color 0.2s;" placeholder="e.g. John Doe">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Email Address</label>
                    <input type="email" name="email" required style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; outline: none;" placeholder="your.name@company.com">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Phone Number (Optional)</label>
                    <input type="text" name="phone" style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; outline: none;" placeholder="+1 (555) 0199">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Target Department</label>
                    <select name="department" style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; background: #ffffff; outline: none;">
                        <option value="General">General Support</option>
                        <option value="Technical">Technical Engineering</option>
                        <option value="Billing">Billing & Accounting</option>
                        <option value="HR">Human Resources</option>
                    </select>
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Subject</label>
                    <input type="text" name="subject" required style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; outline: none;" placeholder="Summary of the issue">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Describe the issue</label>
                    <textarea name="description" rows="4" required style="width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 0.95rem; font-family: inherit; resize: vertical; outline: none;" placeholder="Provide details of your issue..."></textarea>
                </div>
                <div style="margin-bottom: 24px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #334155; font-size: 0.875rem;">Attachment (PDF or Image)</label>
                    <input type="file" id="ai-helpdesk-file" accept="image/*,application/pdf,.docx,.zip,.txt" style="width: 100%; font-size: 0.875rem; color: #64748b;">
                </div>
                <button type="submit" id="ai-helpdesk-submit-btn" style="width: 100%; padding: 12px 20px; background: #2563eb; color: #ffffff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; outline: none;">Submit Ticket</button>
                <div id="ai-helpdesk-response-msg" style="margin-top: 20px; padding: 12px; border-radius: 8px; font-size: 0.9rem; text-align: center; display: none;"></div>
            </form>
        </div>
    `;
    
    const form = document.getElementById('ai-helpdesk-contact-form');
    const submitBtn = document.getElementById('ai-helpdesk-submit-btn');
    const responseMsg = document.getElementById('ai-helpdesk-response-msg');
    
    form.addEventListener('submit', async function(e) {{
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.innerText = 'Submitting your request...';
        submitBtn.style.background = '#93c5fd';
        responseMsg.style.display = 'none';
        
        try {{
            const formData = new FormData(form);
            const fileInput = document.getElementById('ai-helpdesk-file');
            
            const payload = {{
                name: formData.get('name'),
                email: formData.get('email'),
                phone: formData.get('phone'),
                department: formData.get('department'),
                subject: formData.get('subject'),
                description: formData.get('description')
            }};
            
            const submitData = new FormData();
            submitData.append('payload', JSON.stringify(payload));
            if (fileInput.files.length > 0) {{
                submitData.append('attachment', fileInput.files[0]);
            }}
            
            const response = await fetch('{escaped_base_url}/webhook/website', {{
                method: 'POST',
                body: submitData
            }});
            
            const result = await response.json();
            if (response.ok && result.status !== 'Rejected') {{
                responseMsg.style.background = '#f0fdf4';
                responseMsg.style.color = '#166534';
                responseMsg.style.border = '1px solid #bbf7d0';
                responseMsg.innerText = 'Success! Ticket created successfully. ID: ' + (result.ticket_id || 'Submitted');
                form.reset();
            }} else {{
                throw new Error(result.detail || result.reason || 'Failed to submit ticket.');
            }}
        }} catch (error) {{
            responseMsg.style.background = '#fef2f2';
            responseMsg.style.color = '#991b1b';
            responseMsg.style.border = '1px solid #fecaca';
            responseMsg.innerText = 'Error: ' + error.message;
        }} finally {{
            submitBtn.disabled = false;
            submitBtn.innerText = 'Submit Ticket';
            submitBtn.style.background = '#2563eb';
            responseMsg.style.display = 'block';
        }}
    }});
}})();
</script>
"""
