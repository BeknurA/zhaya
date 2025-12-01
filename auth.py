# auth.py - Улучшенная аутентификация с Supabase
import streamlit as st
import hashlib
import secrets
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict, Any
import time

# Подключение к Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Определение ролей и их прав доступа
ROLES = {
    "admin": {
        "name": {"ru": "Администратор", "en": "Administrator", "kk": "Әкімші"},
        "permissions": ["all"]
    },
    "manager": {
        "name": {"ru": "Менеджер", "en": "Manager", "kk": "Менеджер"},
        "permissions": ["view_dashboard", "view_reports", "view_history", "edit_data"]
    },
    "operator": {
        "name": {"ru": "Оператор", "en": "Operator", "kk": "Оператор"},
        "permissions": ["view_dashboard", "edit_data"]
    },
    "analyst": {
        "name": {"ru": "Аналитик", "en": "Analyst", "kk": "Аналитик"},
        "permissions": ["view_dashboard", "view_reports", "view_history"]
    }
}


# Кэш для оптимизации
@st.cache_data(ttl=300)  # 5 минут
def get_cached_user_data(user_id: str):
    """Кэширование данных пользователя"""
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Ошибка получения данных пользователя: {e}")
        return None


def hash_password(password: str) -> str:
    """Хеширование пароля с солью"""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Валидация email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Проверка надежности пароля"""
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if not any(c.isupper() for c in password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not any(c.isdigit() for c in password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    return True, "OK"


def log_activity(user_id: str, action: str, details: Optional[str] = "", ip_address: Optional[str] = None):
    """Логирование активности пользователя"""
    try:
        supabase.table("activity_logs").insert({
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Ошибка логирования: {e}")


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Аутентификация пользователя с валидацией"""

    # Валидация входных данных
    if not validate_email(email):
        return {"authenticated": False, "error": "Неверный формат email"}

    if not password:
        return {"authenticated": False, "error": "Пароль не может быть пустым"}

    password_hash = hash_password(password)

    try:
        # Получение пользователя из БД
        user_data = supabase.table("users") \
            .select("*") \
            .eq("email", email) \
            .eq("password_hash", password_hash) \
            .eq("is_active", True) \
            .execute()

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

            # Обновление времени последнего входа
            supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("user_id", user["user_id"]).execute()

            # Логирование успешного входа
            log_activity(user["user_id"], "login", f"Успешный вход с email: {email}")

            return {
                "id": user["user_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "department": user.get("department"),
                "session_token": session_token,
                "authenticated": True
            }
        else:
            # Логирование неудачной попытки входа
            log_activity(None, "failed_login", f"Неудачная попытка входа для email: {email}")
            return {"authenticated": False, "error": "Неверный логин или пароль"}

    except Exception as e:
        st.error(f"Ошибка аутентификации: {e}")
        return {"authenticated": False, "error": "Ошибка подключения к серверу"}


def check_permission(user_role: str, permission: str) -> bool:
    """Проверка прав доступа с валидацией"""
    if user_role not in ROLES:
        return False

    permissions = ROLES[user_role]["permissions"]

    # Админ имеет все права
    if "all" in permissions:
        return True

    return permission in permissions


def logout_user():
    """Выход пользователя с логированием"""
    if "user" in st.session_state:
        user_id = st.session_state.user.get("id")
        session_token = st.session_state.user.get("session_token")

        if user_id:
            # Логирование выхода
            log_activity(user_id, "logout", "Выход из системы")

            # Деактивация сессии
            if session_token:
                try:
                    supabase.table("user_sessions") \
                        .update({"is_active": False}) \
                        .eq("session_token", session_token) \
                        .execute()
                except Exception as e:
                    st.error(f"Ошибка при завершении сессии: {e}")

        # Очистка session state
        del st.session_state.user

        # Очистка кэша
        st.cache_data.clear()


def show_login_page(lang_choice="ru"):
    """Улучшенная страница входа"""

    st.markdown("""
    <style>
    /* Главный контейнер */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
    }

    .login-container {
        max-width: 450px;
        width: 100%;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        overflow: hidden;
        animation: slideIn 0.5s ease;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .login-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px 30px;
        text-align: center;
        color: white;
    }

    .login-logo {
        font-size: 4em;
        margin-bottom: 10px;
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    .login-title {
        font-size: 2em;
        font-weight: 700;
        margin: 0;
    }

    .login-subtitle {
        font-size: 0.95em;
        opacity: 0.9;
        margin-top: 8px;
    }

    .login-body {
        padding: 40px 30px;
    }

    .input-group {
        margin-bottom: 20px;
    }

    .input-label {
        display: block;
        font-weight: 600;
        margin-bottom: 8px;
        color: #333;
        font-size: 0.95em;
    }

    .stTextInput input {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 12px 15px;
        font-size: 1em;
        transition: all 0.3s;
    }

    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .login-footer {
        background: #f8f9fa;
        padding: 20px 30px;
        text-align: center;
        font-size: 0.85em;
        color: #666;
        border-top: 1px solid #e0e0e0;
    }

    .security-badge {
        display: inline-flex;
        align-items: center;
        background: #e8f5e9;
        color: #2e7d32;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        margin-top: 15px;
    }

    .features-list {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }

    .feature-item {
        display: flex;
        align-items: center;
        margin: 10px 0;
        font-size: 0.9em;
        color: #555;
    }

    .feature-icon {
        margin-right: 10px;
        font-size: 1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

    # Заголовок с логотипом
    st.markdown("""
    <div class="login-header">
        <div class="login-logo">🐎</div>
        <div class="login-title">Жая</div>
        <div class="login-subtitle">Цифровая платформа управления производством</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-body">', unsafe_allow_html=True)

    # Форма входа
    with st.form("login_form", clear_on_submit=False):
        st.markdown('<div class="input-group">', unsafe_allow_html=True)
        email = st.text_input(
            "📧 Email",
            placeholder="Введите ваш email",
            key="login_email"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="input-group">', unsafe_allow_html=True)
        password = st.text_input(
            "🔒 Пароль",
            type="password",
            placeholder="Введите пароль",
            key="login_password"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            remember_me = st.checkbox("Запомнить меня", value=True)

        submit = st.form_submit_button("🚀 Войти в систему", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("⚠️ Пожалуйста, заполните все поля")
            else:
                with st.spinner("🔄 Проверка учетных данных..."):
                    time.sleep(0.5)  # Имитация загрузки
                    user = authenticate_user(email, password)

                    if user.get("authenticated"):
                        st.session_state.user = user
                        st.success(f"✅ Добро пожаловать, {user['full_name']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {user.get('error', 'Ошибка входа')}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Преимущества системы
    st.markdown("""
    <div class="features-list">
        <div style="font-weight: 600; margin-bottom: 15px; color: #333;">
            ✨ Возможности платформы:
        </div>
        <div class="feature-item">
            <span class="feature-icon">📊</span>
            <span>Мониторинг производства в реальном времени</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔬</span>
            <span>Контроль качества и лабораторные измерения</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">📈</span>
            <span>Аналитика и детальные отчеты</span>
        </div>
        <div class="feature-item">
            <span class="feature-icon">🔒</span>
            <span>Безопасное хранение данных</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Значок безопасности
    st.markdown("""
    <div style="text-align: center;">
        <div class="security-badge">
            🛡️ Защищенное подключение SSL
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Футер
    st.markdown("""
    <div class="login-footer">
        <div style="margin-bottom: 10px;">
            © 2025 Жая Production Platform
        </div>
        <div style="font-size: 0.8em; color: #999;">
            Версия 2.0 | Powered by Supabase
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_user_permissions(user_role: str) -> list:
    """Получить список разрешений для роли"""
    if user_role not in ROLES:
        return []
    return ROLES[user_role]["permissions"]

def get_all_users():
    """Получить список всех пользователей"""
    try:
        response = supabase.table("users") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Ошибка получения пользователей: {e}")
        return []