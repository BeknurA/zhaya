# pages/reports.py
import streamlit as st
from database_supabase import init_supabase, fetch_report_data
from ui import get_text, page_header
import pandas as pd
import plotly.express as px

# --- Функции рендеринга (аналогично dashboard.py) ---

def render_chart(report, data):
    """Отображает график (линейный, барный, круговой)."""
    config = report.get('config') or {}
    chart_type = report.get('type')
    title = report.get('name_ru')

    if data.empty:
        st.warning(f"Нет данных для отчета: {title}")
        return

    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown(f"_{report.get('description_ru', '')}_")

    try:
        if chart_type == 'line_chart':
            fig = px.line(data, x=config.get('x_axis'), y=config.get('y_axis'), title=config.get('title'))
        elif chart_type == 'bar_chart':
            fig = px.bar(data, x=config.get('x_axis'), y=config.get('y_axis'), title=config.get('title'))
        elif chart_type == 'pie_chart':
            fig = px.pie(data, names=config.get('names'), values=config.get('values'), title=config.get('title'))
        else:
            st.error(f"Неизвестный тип графика: {chart_type}")
            return

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Ошибка при построении графика '{title}': {e}")

def render_table(report, data):
    """Отображает таблицу."""
    title = report.get('name_ru')
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    st.markdown(f"_{report.get('description_ru', '')}_")
    
    if not data.empty:
        st.dataframe(data, use_container_width=True)
    else:
        st.warning(f"Нет данных для таблицы: {title}")

# --- Основная функция страницы ---

@st.cache_data(ttl=300)
def fetch_all_reports():
    """Получает список всех отчетов из базы данных."""
    supabase = init_supabase()
    if not supabase:
        return []

    try:
        response = supabase.table('reports').select('*').order('name_ru').execute()
        return response.data
    except Exception as e:
        st.error(f"Ошибка при загрузке списка отчетов: {e}")
        return []

def show_reports(lang_choice):
    """
    Отображает страницу, где пользователь может выбрать и просмотреть отчет.
    """
    page_header(get_text("reports_title", lang_choice), "📊")
    st.markdown(get_text("reports_description", lang_choice))
    
    all_reports = fetch_all_reports()
    
    if not all_reports:
        st.info("В системе пока нет созданных отчетов.")
        return

    # Создаем словарь для быстрого доступа к отчетам по имени
    report_dict = {report['name_ru']: report for report in all_reports}
    report_names = list(report_dict.keys())
    
    # Выпадающий список для выбора отчета
    selected_report_name = st.selectbox(
        "Выберите отчет для просмотра:",
        options=report_names,
        index=0
    )
    
    st.markdown("---")

    if selected_report_name:
        # Получаем полную информацию о выбранном отчете
        selected_report = report_dict[selected_report_name]
        
        # Получаем данные для этого отчета
        report_data = fetch_report_data(selected_report['query'])
        
        # Отображаем отчет в зависимости от его типа
        report_type = selected_report.get('type')
        
        if 'chart' in report_type:
            render_chart(selected_report, report_data)
        elif report_type == 'table':
            render_table(selected_report, report_data)
        else:
            st.error(f"Неподдерживаемый тип отчета: '{report_type}'")
