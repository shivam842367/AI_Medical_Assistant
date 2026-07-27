import os
import sys
import tempfile

# Ensure app package directory takes precedence over app.py module name collision
if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

import streamlit as st
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Backend Database, Services & Schemas
from app.database.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.chat import ChatHistory
from app.schemas.user import UserRegister, UserLogin
from app.services.user_service import register_user
from app.services.auth_service import login_user
from app.services.ai_service import chat_with_ai, delete_chat
from app.services.report_analyzer import analyze_report, get_ocr_reader
from app.services.symptom_service import get_symptom_prompt


# ---------------------------------------------------------
# Page Configuration & Rich Aesthetic Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Medical Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom CSS Injection (Google Fonts, Glassmorphism, ECG Animations, Micro-interactions)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap');

    /* Global Typography & Background */
    html, body, [class*="css"] {
        font-family: 'Poppins', 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f0f7ff 0%, #e0f2fe 35%, #f8fafc 100%);
        background-attachment: fixed;
    }

    /* Keyframe Animations */
    @keyframes ecgPulse {
        0% { stroke-dashoffset: 1000; }
        100% { stroke-dashoffset: 0; }
    }
    
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 15px rgba(14, 165, 233, 0.4); transform: scale(1); }
        50% { box-shadow: 0 0 30px rgba(14, 165, 233, 0.8); transform: scale(1.02); }
    }

    @keyframes floatAnim {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }

    /* Hero Header Styling */
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #0284c7 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 24px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 35px -10px rgba(2, 132, 199, 0.35);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .hero-header::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, rgba(255, 255, 255, 0) 70%);
        border-radius: 50%;
        animation: floatAnim 6s ease-in-out infinite;
    }

    .hero-header h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: white !important;
        margin: 0 0 0.4rem 0 !important;
        letter-spacing: -0.5px;
    }

    .hero-header p {
        color: #bae6fd;
        font-size: 1.1rem;
        margin: 0;
        font-weight: 400;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.7);
        box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.05), 0 5px 15px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px -5px rgba(0, 0, 0, 0.08);
    }

    /* ECG Wave Decorative Line */
    .ecg-line {
        height: 40px;
        width: 100%;
        margin-top: 1rem;
    }

    /* Emergency Alert Banner */
    .emergency-alert {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 6px solid #ef4444;
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        color: #991b1b;
        font-weight: 600;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(239, 68, 68, 0.15);
    }

    /* Status Pill Badge */
    .badge-status {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.25rem 0.85rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
    }

    /* Custom Input Controls & Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.25s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #0f172a 50%, #1e293b 100%) !important;
        color: white;
    }

    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Cached Resource Initialization
# ---------------------------------------------------------
@st.cache_resource
def init_database():
    """Ensure database tables are created once."""
    Base.metadata.create_all(bind=engine)
    return True

@st.cache_resource
def load_easyocr():
    """Cache EasyOCR model loading to prevent repeated disk loads."""
    return get_ocr_reader()

# Initialize DB
init_database()


# ---------------------------------------------------------
# Session State Management
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "chat"
if "chat_search" not in st.session_state:
    st.session_state.chat_search = ""
if "selected_chat_id" not in st.session_state:
    st.session_state.selected_chat_id = None
if "report_analysis_result" not in st.session_state:
    st.session_state.report_analysis_result = None
if "report_filename" not in st.session_state:
    st.session_state.report_filename = None


# Helper for DB sessions
def get_db_session():
    return SessionLocal()


# ---------------------------------------------------------
# Rich Authentication Page (With Brain Network & ECG Visuals)
# ---------------------------------------------------------
def render_auth_page():
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
            <div style="display: inline-block; padding: 0.5rem 1.2rem; background: rgba(14, 165, 233, 0.1); border-radius: 50px; margin-bottom: 0.75rem;">
                <span style="color: #0284c7; font-weight: 700; font-size: 0.9rem;">🩺 AI-POWERED HEALTHCARE PLATFORM</span>
            </div>
            <h1 style="color: #0f172a; font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin: 0;">AI Medical Assistant</h1>
            <p style="color: #64748b; font-size: 1.15rem; max-width: 600px; margin: 0.5rem auto 0 auto;">
                Next-generation medical intelligence. Instant clinical guidance, symptom analysis, and automated report interpretation.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Glassmorphism Container
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register Account"])

        # LOGIN TAB
        with tab_login:
            st.markdown("<h3 style='margin-top:0.5rem;'>Welcome Back</h3>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("Email Address", placeholder="patient@example.com")
                login_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Sign In to Account ➔", use_container_width=True, type="primary")

                if submit_login:
                    if not login_email or not login_password:
                        st.error("Please enter your email and password.")
                    else:
                        db = get_db_session()
                        try:
                            login_data = UserLogin(email=login_email.strip(), password=login_password.strip())
                            result = login_user(db, login_data)
                            user_obj = db.query(User).filter(User.email == login_email.strip()).first()
                            if user_obj:
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id": user_obj.id,
                                    "full_name": user_obj.full_name,
                                    "email": user_obj.email,
                                    "token": result.get("access_token")
                                }
                                st.success("Login successful! Redirecting...")
                                st.rerun()
                        except Exception as e:
                            st.error(getattr(e, "detail", "Invalid email or password."))
                        finally:
                            db.close()

        # REGISTER TAB
        with tab_register:
            st.markdown("<h3 style='margin-top:0.5rem;'>Create Free Account</h3>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input("Full Name", placeholder="Jane Doe")
                reg_email = st.text_input("Email Address", placeholder="jane@example.com")
                reg_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_reg = st.form_submit_button("Complete Registration ➔", use_container_width=True, type="primary")

                if submit_reg:
                    if not reg_name or not reg_email or not reg_password:
                        st.error("Please complete all registration fields.")
                    else:
                        db = get_db_session()
                        try:
                            reg_data = UserRegister(
                                full_name=reg_name.strip(),
                                email=reg_email.strip(),
                                password=reg_password.strip()
                            )
                            user = register_user(db, reg_data)
                            st.success("Account created! Switch to Sign In to log in.")
                        except Exception as e:
                            st.error(f"Registration error: {str(e)}")
                        finally:
                            db.close()

        st.markdown('</div>', unsafe_allow_html=True)

        # SVG ECG Wave Animation Bar
        st.markdown("""
            <div style="text-align: center; margin-top: 1.5rem;">
                <svg width="100%" height="50" viewBox="0 0 500 50" style="overflow: visible;">
                    <path d="M0,25 L120,25 L135,10 L150,40 L165,5 L180,45 L195,25 L500,25" 
                          fill="none" stroke="#0284c7" stroke-width="2.5" 
                          stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# Sidebar Component (Dark Medical Theme)
# ---------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        # Header Badge
        st.markdown(f"""
            <div style="padding: 1.2rem 0; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.2rem;">
                <h2 style="margin: 0; font-size: 1.4rem; font-weight: 700; color: white;">🩺 AI Medical</h2>
                <div style="margin-top: 0.5rem;">
                    <span class="badge-status">🟢 Engine Online</span>
                </div>
                <p style="margin: 0.6rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">👤 {st.session_state.user['full_name']}</p>
            </div>
        """, unsafe_allow_html=True)

        # Navigation Bar
        nav = st.radio(
            "Quick Navigation",
            options=["💬 AI Chat Consultation", "📑 Report Analyzer", "🩺 Symptom Checker", "📜 Saved Consultations"],
            index=0 if st.session_state.active_nav == "chat"
            else 1 if st.session_state.active_nav == "report"
            else 2 if st.session_state.active_nav == "symptom"
            else 3
        )

        if nav.startswith("💬"):
            st.session_state.active_nav = "chat"
        elif nav.startswith("📑"):
            st.session_state.active_nav = "report"
        elif nav.startswith("🩺"):
            st.session_state.active_nav = "symptom"
        elif nav.startswith("📜"):
            st.session_state.active_nav = "history"

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1.2rem 0;'>", unsafe_allow_html=True)

        # Recent Consultations Search
        st.markdown("<h4 style='color: white; margin-bottom: 0.5rem;'>🔍 Search History</h4>", unsafe_allow_html=True)
        search_query = st.text_input("Search term...", value=st.session_state.chat_search, key="sidebar_search", label_visibility="collapsed")
        st.session_state.chat_search = search_query

        db = get_db_session()
        try:
            query = db.query(ChatHistory).filter(ChatHistory.user_id == st.session_state.user["id"])
            if search_query.strip():
                query = query.filter(
                    (ChatHistory.question.ilike(f"%{search_query.strip()}%")) |
                    (ChatHistory.answer.ilike(f"%{search_query.strip()}%"))
                )
            recent_chats = query.order_by(ChatHistory.created_at.desc()).limit(6).all()

            if recent_chats:
                for c in recent_chats:
                    q_label = c.question[:26] + "..." if len(c.question) > 26 else c.question
                    col_item, col_del = st.columns([5, 1])
                    with col_item:
                        if st.button(f"💬 {q_label}", key=f"chat_nav_{c.id}", use_container_width=True):
                            st.session_state.selected_chat_id = c.id
                            st.session_state.active_nav = "chat"
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_nav_{c.id}", help="Delete consultation"):
                            delete_chat(db, c.id, st.session_state.user["id"])
                            if st.session_state.selected_chat_id == c.id:
                                st.session_state.selected_chat_id = None
                            st.rerun()
            else:
                st.caption("No past consultations.")
        finally:
            db.close()

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1.2rem 0;'>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.selected_chat_id = None
            st.rerun()


# ---------------------------------------------------------
# View 1: AI Chat Assistant
# ---------------------------------------------------------
def render_chat_view():
    st.markdown("""
        <div class="hero-header">
            <h1>💬 AI Medical Consultation</h1>
            <p>Real-time healthcare guidance, emergency analysis, and clinical insights.</p>
        </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        user_chats = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == st.session_state.user["id"])
            .order_by(ChatHistory.created_at.asc())
            .all()
        )

        # Action Bar: New Chat
        col_new, col_blank = st.columns([1, 4])
        with col_new:
            if st.button("+ New Conversation", type="primary"):
                st.session_state.selected_chat_id = None
                st.rerun()

        # Chat Message History
        st.markdown('<div class="glass-card" style="padding: 1.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
        if not user_chats:
            st.info("👋 Hello! I am your AI Medical Assistant. Ask any health or medical question to begin.")
        else:
            for c in user_chats:
                st.chat_message("user").write(c.question)
                st.chat_message("assistant").write(c.answer)
        st.markdown('</div>', unsafe_allow_html=True)

        # User Input Box
        if user_prompt := st.chat_input("Describe your medical question or symptoms (e.g., 'What are common causes of fatigue?')..."):
            st.chat_message("user").write(user_prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing query and formulating response..."):
                    res = chat_with_ai(db=db, message=user_prompt, user_id=st.session_state.user["id"])
                    st.write(res.response)
            st.rerun()

    finally:
        db.close()


# ---------------------------------------------------------
# View 2: Medical Report Analyzer
# ---------------------------------------------------------
def render_report_view():
    st.markdown("""
        <div class="hero-header" style="background: linear-gradient(135deg, #0d9488 0%, #059669 50%, #047857 100%);">
            <h1>📑 Medical Report Analyzer</h1>
            <p>Upload laboratory reports, blood tests, or diagnostic scans (PDF/Image) for automated analysis.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📤 Upload Medical Document")
        uploaded_file = st.file_uploader(
            "Select report document (.pdf, .png, .jpg, .jpeg)",
            type=["pdf", "png", "jpg", "jpeg"]
        )

        if uploaded_file is not None:
            st.success(f"Selected: **{uploaded_file.name}** ({uploaded_file.size // 1024} KB)")

            if st.button("🚀 Analyze Report Document", type="primary", use_container_width=True):
                with st.spinner("🤖 Running OCR text extraction & AI diagnostic analysis..."):
                    ext = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    try:
                        ocr_reader = load_easyocr()
                        analysis_output = analyze_report(tmp_path, ocr_reader=ocr_reader)
                        st.session_state.report_analysis_result = analysis_output
                        st.session_state.report_filename = uploaded_file.name
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📋 AI Diagnostic Breakdown")
        if st.session_state.report_analysis_result:
            st.markdown(st.session_state.report_analysis_result)

            st.download_button(
                label="📥 Download Diagnostic Report (.txt)",
                data=st.session_state.report_analysis_result,
                file_name=f"Report_Analysis_{st.session_state.report_filename or 'Medical'}.txt",
                mime="text/plain"
            )
        else:
            st.info("Upload a diagnostic report file on the left and click **Analyze Report Document** to view the findings.")
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# View 3: Symptom Checker
# ---------------------------------------------------------
def render_symptom_view():
    st.markdown("""
        <div class="hero-header" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #6d28d9 100%);">
            <h1>🩺 Structured Symptom Checker</h1>
            <p>Input clinical symptoms for structured evaluation, home care guidance, and doctor consultation advice.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("symptom_form"):
        symptoms_input = st.text_area(
            "Describe your symptoms in detail:",
            placeholder="E.g., I have experienced a sore throat, mild fever (100°F), and headache for the past 2 days...",
            height=130
        )
        submit_symptoms = st.form_submit_button("🔍 Evaluate Symptoms ➔", type="primary")

    if submit_symptoms:
        if not symptoms_input.strip():
            st.warning("Please enter your symptoms before submitting.")
        else:
            with st.spinner("Evaluating symptoms against clinical criteria..."):
                formatted_prompt = get_symptom_prompt(symptoms_input.strip())
                db = get_db_session()
                try:
                    res = chat_with_ai(db=db, message=formatted_prompt, user_id=st.session_state.user["id"])
                    st.markdown("### 📊 Clinical Evaluation Report")
                    st.markdown(res.response)
                finally:
                    db.close()
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# View 4: Saved Consultation History
# ---------------------------------------------------------
def render_history_view():
    st.markdown("""
        <div class="hero-header" style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%);">
            <h1>📜 Consultation History Archive</h1>
            <p>Review past medical queries, diagnostic outputs, and health advice history.</p>
        </div>
    """, unsafe_allow_html=True)

    db = get_db_session()
    try:
        chats = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == st.session_state.user["id"])
            .order_by(ChatHistory.created_at.desc())
            .all()
        )

        if not chats:
            st.info("No consultation history records found.")
            return

        for c in chats:
            st.markdown('<div class="glass-card" style="padding: 1.25rem;">', unsafe_allow_html=True)
            with st.expander(f"💬 {c.question[:65]}... ({c.created_at.strftime('%b %d, %Y %I:%M %p')})"):
                st.markdown(f"**Patient Query:**\n{c.question}")
                st.markdown("---")
                st.markdown(f"**AI Guidance:**\n{c.answer}")

                if st.button("🗑️ Delete Record", key=f"hist_del_{c.id}"):
                    delete_chat(db, c.id, st.session_state.user["id"])
                    st.success("Deleted!")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    finally:
        db.close()


# ---------------------------------------------------------
# Main App Router
# ---------------------------------------------------------
def main():
    if not st.session_state.authenticated or not st.session_state.user:
        render_auth_page()
    else:
        render_sidebar()

        if st.session_state.active_nav == "chat":
            render_chat_view()
        elif st.session_state.active_nav == "report":
            render_report_view()
        elif st.session_state.active_nav == "symptom":
            render_symptom_view()
        elif st.session_state.active_nav == "history":
            render_history_view()


if __name__ == "__main__":
    main()
