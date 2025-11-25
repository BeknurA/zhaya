# app.py - Главный файл с улучшенной аутентификацией
import streamlit as st
from ui import get_text, LANG
from auth import show_login_page, logout_user, check_permission, ROLES, log_activity
from database_supabase import clear_all_caches

# Импорт страниц (удалены ml_training и new_data_input)
from pages.home import show_home
from pages.production import show_production_process
from pages.regression import show_regression_models
from pages.ph_modeling import show_ph_modeling
from pages.seabuckthorn import show_seabuckthorn_analysis
from pages.data_exploration import show_data_exploration
from pages.history_db import show_history_db
from pages.dashboard import show_dashboard
from pages.reports import show_reports
from pages.supabase_test import show_supabase_test

# Настройки страницы
st.set_page_config(
    page_title="Платформа Жая — Производство",
    layout="wide",
    page_icon="🐎",
    initial_sidebar_state="expanded"
)

# Стили приложения
st.markdown("""
<style>
/* Глобальные настройки */
.stApp {
    background-color: #111111;
    color: #f0f0f0;
}

/* Скрыть автоматическое меню Streamlit */
[data-testid="stSidebarNav"] {
    display: none;
}

/* Fade-In анимация */
.fade-in {
    animation: fadeIn ease 0.5s;
}
@keyframes fadeIn {
    0% {opacity:0; transform:translateY(6px)}
    100% {opacity:1; transform:translateY(0)}
}

/* Sidebar стили */
[data-testid="stSidebar"] {
    background-color: #1f1f1f;
    box-shadow: 2px 0px 8px rgba(0,0,0,0.5);
}

/* Метрики */
[data-testid="stMetric"] {
    background-color: #2a2a2a;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 5px solid #0d6efd;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    transition: all 0.3s;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.6);
}

/* Кнопки */
.stButton button {
    background-color: #495057;
    color: white;
    border-radius: 5px;
    border: none;
    transition: all 0.3s ease;
    padding: 10px 15px;
    font-weight: 600;
}

.stButton button:hover {
    background-color: #6c757d;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

/* Текст */
h1, h2, h3, h4, h5, h6, .stMarkdown, .stText {
    color: #f0f0f0 !important;
}

/* Карточка пользователя */
.user-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    color: white;
    text-align: center;
}

.user-role {
    font-size: 0.85em;
    opacity: 0.9;
    margin-top: 5px;
}

/* Уведомления */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 600;
    margin-left: 8px;
}

.status-online {
    background: #d4edda;
    color: #155724;
}

.status-offline {
    background: #f8d7da;
    color: #721c24;
}
</style>
""", unsafe_allow_html=True)

# =================================================================
# ПРОВЕРКА АУТЕНТИФИКАЦИИ
# =================================================================
if "user" not in st.session_state or not st.session_state.user.get("authenticated", False):
    show_login_page()
    st.stop()

# =================================================================
# ГЛАВНЫЙ ИНТЕРФЕЙС
# =================================================================

user = st.session_state.user
user_role = user.get("role", "operator")
lang_codes = list(LANG.keys())

# Настройка языка
_lang_name_map = {
    "ru": "Русский",
    "en": "English",
    "kk": "Қазақша",
}
lang_names = [_lang_name_map.get(code, code) for code in lang_codes]

if "lang_choice" not in st.session_state:
    st.session_state.lang_choice = "ru"

# =================================================================
# SIDEBAR: Профиль и навигация
# =================================================================
with st.sidebar:
    # Карточка пользователя
    role_name = ROLES.get(user_role, {}).get("name", {}).get(st.session_state.lang_choice, user_role)

    st.markdown(f"""
    <div class="user-badge">
        <div style='font-size: 2em;'>👤</div>
        <div style='font-weight: 600; font-size: 1.1em;'>{user.get('full_name', 'Пользователь')}</div>
        <div class="user-role">{role_name}</div>
        <span class="status-badge status-online">● Онлайн</span>
    </div>
    """, unsafe_allow_html=True)

    # Выбор языка
    try:
        current_index = lang_codes.index(st.session_state.lang_choice)
    except ValueError:
        current_index = 0

    selected_name = st.selectbox("🌐 Язык / Language", lang_names, index=current_index)
    selected_code = lang_codes[lang_names.index(selected_name)]
    st.session_state.lang_choice = selected_code
    lang_choice = st.session_state.lang_choice

    st.markdown("---")

    # Навигация с учетом прав доступа
    st.markdown("### 📂 Навигация")

    page_options = []

    # Dashboard (доступен всем)
    if check_permission(user_role, "view_dashboard"):
        page_options.append(("🎯 Dashboard", "dashboard"))

    # Главная страница
    page_options.append((get_text("menu_home", lang_choice), "home"))

    # Процесс производства
    page_options.append((get_text("menu_production_process", lang_choice), "production"))

    # Регрессионные модели
    page_options.append((get_text("menu_regression_models", lang_choice), "regression"))

    # pH моделирование
    page_options.append((get_text("menu_ph_modeling", lang_choice), "ph_modeling"))

    # Анализ облепихи
    page_options.append((get_text("menu_seabuckthorn_analysis", lang_choice), "seabuckthorn"))

    # Исследование данных
    page_options.append((get_text("menu_data_exploration", lang_choice), "data_exploration"))

    # История / БД (только для аналитиков и выше)
    if check_permission(user_role, "view_history"):
        page_options.append((get_text("menu_history_db", lang_choice), "history_db"))

    # Отчеты (для менеджеров и аналитиков)
    if check_permission(user_role, "view_reports"):
        page_options.append(("📊 Отчеты", "reports"))

    # Тест Supabase (только для админов)
    if user_role == "admin":
        page_options.append(("🔧 Тест Supabase", "supabase_test"))

    # Отображение меню
    page_labels = [item[0] for item in page_options]
    page_keys = [item[1] for item in page_options]

    if "selected_page" not in st.session_state:
        st.session_state.selected_page = page_keys[0]

    # Радио-кнопки для навигации
    selected_label = st.radio(
        "Выберите раздел:",
        page_labels,
        index=page_keys.index(st.session_state.selected_page) if st.session_state.selected_page in page_keys else 0
    )

    # Определение выбранной страницы
    selected_index = page_labels.index(selected_label)
    new_page = page_keys[selected_index]

    # Логирование перехода на новую страницу
    if new_page != st.session_state.selected_page:
        log_activity(user.get("id"), "navigate", f"Переход на страницу: {new_page}")

    st.session_state.selected_page = new_page

    st.markdown("---")

    # Быстрые действия
    if check_permission(user_role, "edit_data"):
        st.markdown("### ⚡ Быстрые действия")
        if st.button("🆕 Новая партия", use_container_width=True):
            st.info("Функция добавления новой партии")

    st.markdown("---")

    # Системная информация
    st.caption(f"🕒 Версия: 2.0 Production")
    st.caption(f"📅 {user.get('email', 'user')}")

    # Очистка кэша (только для админов)
    if user_role == "admin":
        if st.button("🔄 Очистить кэш", use_container_width=True):
            clear_all_caches()
            st.success("✅ Кэш очищен")
            log_activity(user.get("id"), "clear_cache", "Очистка кэша приложения")

    # Кнопка выхода
    if st.button("🚪 Выйти из системы", key="logout_btn", use_container_width=True):
        logout_user()
        st.rerun()

# =================================================================
# РОУТИНГ СТРАНИЦ
# =================================================================
page = st.session_state.selected_page

if page == "dashboard":
    show_dashboard(lang_choice)
elif page == "supabase_test" and user_role == "admin":
    show_supabase_test()
elif page == "home":
    show_home(lang_choice)
elif page == "production":
    show_production_process(lang_choice)
elif page == "regression":
    show_regression_models(lang_choice)
elif page == "ph_modeling":
    show_ph_modeling(lang_choice)
elif page == "seabuckthorn":
    show_seabuckthorn_analysis(lang_choice)
elif page == "data_exploration":
    show_data_exploration(lang_choice)
elif page == "history_db":
    if check_permission(user_role, "view_history"):
        show_history_db(lang_choice)
    else:
        st.error("❌ Доступ запрещен")
elif page == "reports":
    if check_permission(user_role, "view_reports"):
        show_reports(lang_choice)
    else:
        st.error("❌ Доступ запрещен")
else:
    st.warning("Страница не найдена")