# pages/dashboard.py
import streamlit as st
import plotly.express as px
import pandas as pd
from database_supabase import fetch_dashboard_config, fetch_report_data
from ui import get_text, page_header

def render_kpi(report, data):
    """Отображает метрику KPI."""
    config = report['reports']['config'] or {}
    title = report['reports']['name_ru']

    # Предполагаем, что запрос для KPI возвращает одно значение
    if not data.empty:
        value = data.iloc[0, 0]
        st.metric(
            label=title,
            value=f"{config.get('prefix', '')}{value:.{config.get('decimals', 0)}f}{config.get('suffix', '')}"
        )
    else:
        st.metric(label=title, value="Нет данных")

def render_chart(report, data):
    """Отображает график (линейный, барный, круговой)."""
    config = report['reports']['config'] or {}
    chart_type = report['reports']['type']
    title = report['reports']['name_ru']

    if data.empty:
        st.warning(f"Нет данных для отчета: {title}")
        return

    st.markdown(f"<h5>{title}</h5>", unsafe_allow_html=True)

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
    title = report['reports']['name_ru']
    st.markdown(f"<h5>{title}</h5>", unsafe_allow_html=True)
    if not data.empty:
        st.dataframe(data, use_container_width=True)
    else:
        st.warning(f"Нет данных для таблицы: {title}")

def show_dashboard(lang_choice):
    """
    Главная функция для отображения дашборда.
    Загружает конфигурацию из БД и рендерит отчеты.
    """
    page_header(get_text("dashboard_title", lang_choice), "🎯")

    # ID дашборда, который мы хотим отобразить.
    # В будущем можно сделать выбор дашборда.
    DASHBOARD_ID = 1

    dashboard_info, reports_config = fetch_dashboard_config(DASHBOARD_ID)

    if not dashboard_info:
        st.error("Не удалось загрузить дашборд. Проверьте конфигурацию в базе данных.")
        return

    st.markdown(f"_{get_text(dashboard_info.get('description_ru', ''), lang_choice)}_")
    st.markdown("---")

    if not reports_config:
        st.info("На этом дашборде пока нет отчетов.")
        return

    # Сортируем отчеты по их расположению
    reports_config.sort(key=lambda r: (r['position_row'], r['position_col']))

    # Создаем динамическую сетку для отчетов
    # Определяем максимальное количество колонок
    max_cols = max(r['position_col'] + r['width'] for r in reports_config) if reports_config else 1

    # Группируем отчеты по строкам
    rows = {}
    for report in reports_config:
        row_num = report['position_row']
        if row_num not in rows:
            rows[row_num] = []
        rows[row_num].append(report)

    # Отображаем каждую строку
    for row_num in sorted(rows.keys()):
        cols = st.columns(max_cols)
        for report in rows[row_num]:
            col_index = report['position_col']
            col_span = report['width']

            # Получаем данные для отчета
            report_data = fetch_report_data(report['reports']['query'])

            # Выбираем нужные колонки и рендерим отчет
            with cols[col_index]:
                report_type = report['reports']['type']

                if report_type == 'kpi':
                    render_kpi(report, report_data)
                elif 'chart' in report_type:
                    render_chart(report, report_data)
                elif report_type == 'table':
                    render_table(report, report_data)
                else:
                    st.error(f"Неизвестный тип отчета: {report_type}")
