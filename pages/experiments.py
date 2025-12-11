# pages/experiments.py - Экспериментальные исследования
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


def show_experiments(lang_choice="ru"):
    """Страница экспериментальных исследований"""

    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)

    # Заголовок
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
        <h1 style='margin: 0; color: white;'>🔬 Экспериментальные исследования</h1>
        <p style='margin: 10px 0 0 0; opacity: 0.95; font-size: 1.05em;'>
            Протоколы опытов по переработке молока и мяса с регистрацией параметров
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Табы для разных типов экспериментов
    tab1, tab2, tab3 = st.tabs([
        "🥩 Опыты с мясом (Жая)",
        "🥛 Опыты с молоком",
        "📊 Прогнозирование pH"
    ])

    # ===== ТАБ 1: ОПЫТЫ С МЯСОМ =====
    with tab1:
        st.header("Эксперименты с мясными продуктами")

        # Протокол эксперимента
        st.subheader("📋 Протокол эксперимента №1")

        exp_info = {
            "Дата проведения": "15.11.2024",
            "Ответственный": "Лаборант Айгуль С.",
            "Тип продукта": "Жая (цельномышечная)",
            "Партия": "JY-2024-112",
            "Концентрация экстракта": "5%"
        }

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Дата", exp_info["Дата проведения"])
        with col2:
            st.metric("Партия", exp_info["Партия"])
        with col3:
            st.metric("Экстракт", exp_info["Концентрация экстракта"])

        st.markdown("---")

        # Таблица экспериментальных данных
        st.subheader("📊 Зарегистрированные параметры")

        # Данные эксперимента
        exp_data = pd.DataFrame({
            'Время (ч)': [0, 24, 48, 72, 96, 120, 144],
            'Температура (°C)': [2.1, 2.3, 1.9, 2.0, 2.2, 2.1, 2.0],
            'Влажность (%)': [71.2, 70.8, 69.5, 68.9, 68.2, 67.8, 67.5],
            'pH': [6.52, 6.31, 6.08, 5.82, 5.61, 5.45, 5.32],
            'Масса (г)': [1000, 998, 995, 990, 985, 980, 975],
            'Aw': [0.96, 0.95, 0.93, 0.92, 0.90, 0.89, 0.88]
        })

        st.dataframe(exp_data, use_container_width=True, hide_index=True)

        # График pH
        st.subheader("📈 Динамика pH (обратная зависимость от времени)")

        fig_ph = go.Figure()

        fig_ph.add_trace(go.Scatter(
            x=exp_data['Время (ч)'],
            y=exp_data['pH'],
            mode='lines+markers',
            name='Экспериментальные данные',
            line=dict(color='#667eea', width=3),
            marker=dict(size=10, line=dict(width=2, color='white'))
        ))

        # Зона оптимального pH
        fig_ph.add_hrect(
            y0=5.1, y1=5.6,
            fillcolor="green", opacity=0.1,
            annotation_text="Целевой диапазон pH",
            annotation_position="top left"
        )

        fig_ph.update_layout(
            title="Зависимость pH от времени ферментации",
            xaxis_title="Время ферментации (часы)",
            yaxis_title="pH",
            height=450,
            template='plotly_white',
            hovermode='x unified'
        )

        st.plotly_chart(fig_ph, use_container_width=True)

        # Проверка точности прогноза
        st.subheader("🎯 Прогнозирование pH с точностью ±0.05")

        col_pred1, col_pred2, col_pred3 = st.columns(3)

        with col_pred1:
            target_time = st.slider("Время (ч)", 0, 144, 72, 12)

        with col_pred2:
            # Модель pH
            pH0 = 6.52
            pH_inf = 5.1
            k = 0.012
            predicted_ph = pH_inf + (pH0 - pH_inf) * np.exp(-k * target_time)

            st.metric("Прогноз pH", f"{predicted_ph:.2f}")

        with col_pred3:
            # Фактическое значение
            actual_ph = np.interp(target_time, exp_data['Время (ч)'], exp_data['pH'])
            error = abs(predicted_ph - actual_ph)

            delta_color = "normal" if error <= 0.05 else "inverse"
            st.metric(
                "Погрешность",
                f"±{error:.3f}",
                delta="✅ Точность достигнута" if error <= 0.05 else "⚠️ Превышена",
                delta_color=delta_color
            )

        # Результаты
        st.markdown(f"""
        <div style='background: {"#2A453C" if error <= 0.05 else "#453C2A"}; 
                    color: #F0F0F0; /* Принудительно светлый текст (F0F0F0) */
                    padding: 15px; 
                    border-radius: 10px; 
                    border-left: 5px solid {"#4CAF50" if error <= 0.05 else "#FFC107"}; /* Яркая граница */
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);'>
            <b>{"✅ Прогноз достоверен" if error <= 0.05 else "⚠️ Требуется калибровка модели"}</b><br>
            Через <b>{target_time} часов</b> прогнозируемый pH: <b>{predicted_ph:.2f}</b><br>
            Фактический pH: <b>{actual_ph:.2f}</b><br>
            Погрешность: <b>{error:.3f}</b> ({"в пределах нормы" if error <= 0.05 else "превышает допуск ±0.05"})
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Температура и влажность
        st.subheader("🌡️ Контроль температуры и влажности")

        fig_temp_hum = go.Figure()

        fig_temp_hum.add_trace(go.Scatter(
            x=exp_data['Время (ч)'],
            y=exp_data['Температура (°C)'],
            name='Температура (°C)',
            yaxis='y',
            line=dict(color='#ff6b6b', width=2)
        ))

        fig_temp_hum.add_trace(go.Scatter(
            x=exp_data['Время (ч)'],
            y=exp_data['Влажность (%)'],
            name='Влажность (%)',
            yaxis='y2',
            line=dict(color='#4ecdc4', width=2)
        ))

        fig_temp_hum.update_layout(
            title="Температура и влажность в процессе посола",
            xaxis=dict(title="Время (ч)"),
            yaxis=dict(title="Температура (°C)", side='left', range=[0, 5]),
            yaxis2=dict(title="Влажность (%)", side='right', overlaying='y', range=[60, 75]),
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )

        st.plotly_chart(fig_temp_hum, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)