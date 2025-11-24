# auth.py - Аутентификация через Supabase с ролями
import streamlit as st
import hashlib
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional

# Подключение к Supabase через Streamlit Secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Роли пользователей и их права
ROLES = {
    "admin": {"permissions": ["all"]},
    "manager": {"permissions": [ "view_reports", "edit_data", "view_history"]},
    "operator": {"permissions": ["view_dashboard", "edit_data"]},
    "analyst": {"permissions": ["view_dashboard", "view_reports", "view_history"]},
}

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email: str, password: str) -> dict:
    """Аутентификация пользователя через Supabase"""
    password_hash = hash_password(password)
    
    user_data = supabase.table("users").select("*").eq("email", email).eq("password_hash", password_hash).eq("is_active", True).execute()
    

    
    if user_data.data and len(user_data.data) > 0:
        user = user_data.data[0]
        # Создание сессии
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=8)
        supabase.table("user_sessions").insert({
            "user_id": user["user_id"],
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "is_active": True
        }).execute()
        log_activity(user["user_id"], "login", "Успешный вход")
        return {
            "id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "session_token": session_token,
            "authenticated": True
        }
    return {"authenticated": False, "error": "Неверный логин или пароль"}

def log_activity(user_id: str, action: str, details: Optional[str] = ""):
    """Логирование активности"""
    supabase.table("activity_logs").insert({
        "user_id": user_id,
        "action": action,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

def check_permission(user_role: str, permission: str) -> bool:
    """Проверка прав доступа"""
    if user_role not in ROLES:
        return False
    permissions = ROLES[user_role]["permissions"]
    return "all" in permissions or permission in permissions

def logout_user():
    """Выход пользователя из системы"""
    if "user" in st.session_state:
        user_id = st.session_state.user.get("id")
        if user_id:
            log_activity(user_id, "logout", "Выход из системы")
            supabase.table("user_sessions").update({"is_active": False}).eq("user_id", user_id).execute()
        del st.session_state.user

def get_all_users():
    """Получение всех пользователей"""
    users_data = supabase.table("users").select("*").execute()
    return users_data.data

def show_login_page(lang_choice="ru"):
    """Страница входа в Streamlit"""
    st.markdown("""
    <style>
    .login-container {max-width: 450px;margin: 80px auto;padding: 40px;background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);}
    .login-card {background:white;padding:40px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.1);}
    .login-title {text-align:center;color:#667eea;font-size:2.5em;font-weight:700;margin-bottom:10px;}
    .login-subtitle {text-align:center;color:#666;margin-bottom:30px;}
    .demo-credentials {background:#f8f9fa;padding:15px;border-radius:8px;margin-top:20px;font-size:0.9em;border-left:4px solid #667eea;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🐎 Жая</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Цифровая платформа управления производством</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("👤 Email", placeholder="Введите email")
        password = st.text_input("🔒 Пароль", type="password", placeholder="Введите пароль")
        submit = st.form_submit_button("🚀 Войти")

        if submit:
            if not email or not password:
                st.error("⚠️ Заполните все поля")
            else:
                user = authenticate_user(email, password)
                if user.get("authenticated"):
                    st.session_state.user = user
                    st.success(f"✅ Добро пожаловать, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {user.get('error','Неверный логин или пароль')}")

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("© 2025 Жая Production Platform | Версия 2.0")
      # <- посмотри, что реально возвращается

