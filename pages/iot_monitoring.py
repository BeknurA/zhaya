# pages/iot_monitoring.py - Мониторинг IoT датчиков в реальном времени
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import time

# Импорт функций для работы с MQTT и БД
from database_supabase import fetch_iot_sensor_data

def get_latest_sensor_data(batch_id=None, limit=1000):
    """Wrapper для получения данных датчиков"""
    try:
        return fetch_iot_sensor_data(batch_id=batch_id, limit=limit)
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return []

def send_actuator_command(batch_id, actuator_name, set_value, changed_by="streamlit"):
    """Отправка команды актуатору (заглушка для демо)"""
    try:
        from database_supabase import init_supabase
        supabase = init_supabase()
        if not supabase:
            return False
        
        log_data = {
            "batch_id": batch_id,
            "actuator_name": actuator_name,
            "set_value": set_value,
            "previous_value": 0,
            "changed_by": changed_by
        }
        
        result = supabase.table("actuator_logs").insert(log_data).execute()
        return bool(result.data)
    except Exception as e:
        st.error(f"Ошибка отправки команды: {e}")
        return False


def show_iot_monitoring(lang_choice="ru"):
    """Страница мониторинга IoT датчиков"""
    
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
    
    # Заголовок
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);'>
        <h1 style='margin: 0; color: white;'>📡 IoT Мониторинг производства</h1>
        <p style='margin: 10px 0 0 0; opacity: 0.95; font-size: 1.05em;'>
            Мониторинг датчиков и управление процессом в реальном времени
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - управление
    with st.sidebar:
        st.header("⚙️ Управление мониторингом")
        
        # Выбор партии
        batch_id = st.number_input("ID партии", min_value=1, value=1, step=1)
        
        # Автообновление
        auto_refresh = st.checkbox("🔄 Автообновление", value=True)
        
        if auto_refresh:
            refresh_interval = st.slider("Интервал (сек)", 1, 30, 5)
        else:
            refresh_interval = None
        
        # Период просмотра
        time_window = st.selectbox(
            "Период просмотра",
            ["Последние 5 мин", "Последние 15 мин", "Последние 30 мин", 
             "Последний час", "Последние 3 часа", "Последние 24 часа"]
        )
        
        st.markdown("---")
        
        # Ручное обновление
        if st.button("🔄 Обновить сейчас", use_container_width=True):
            st.rerun()
    
    # Получение данных из БД
    with st.spinner("📊 Загрузка данных датчиков..."):
        try:
            sensor_data_raw = get_latest_sensor_data(batch_id=batch_id, limit=1000)
            
            # Проверка типа данных
            if isinstance(sensor_data_raw, pd.DataFrame):
                sensor_data = sensor_data_raw.to_dict('records') if not sensor_data_raw.empty else []
            else:
                sensor_data = sensor_data_raw if sensor_data_raw else []
                
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")
            sensor_data = []
    
    if not sensor_data or len(sensor_data) == 0:
        st.warning(f"⚠️ Нет данных для партии ID: {batch_id}")
        st.info("""
        💡 **Запустите симулятор:**
        
        ```bash
        python mqtt_client.py
        ```
        
        Симулятор будет генерировать данные датчиков и отправлять их через MQTT в БД.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Преобразование в DataFrame
    df = pd.DataFrame(sensor_data)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    
    # Фильтрация по времени
    time_filters = {
        "Последние 5 мин": 5,
        "Последние 15 мин": 15,
        "Последние 30 мин": 30,
        "Последний час": 60,
        "Последние 3 часа": 180,
        "Последние 24 часа": 1440
    }
    
    minutes_ago = time_filters.get(time_window, 30)
    cutoff_time = pd.Timestamp.now(tz='UTC') - timedelta(minutes=minutes_ago)
    df = df[df['time'] >= cutoff_time]
    
    # === СТАТИСТИКА В РЕАЛЬНОМ ВРЕМЕНИ ===
    st.subheader("📊 Текущие показатели")
    
    # Получение последних значений по каждому типу датчика
    latest_values = {}
    for sensor_type in df['sensor_type'].unique():
        sensor_df = df[df['sensor_type'] == sensor_type].sort_values('time', ascending=False)
        if not sensor_df.empty:
            latest_values[sensor_type] = sensor_df.iloc[0]
    
    # Отображение метрик
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'temperature' in latest_values:
            temp_data = latest_values['temperature']
            temp_value = temp_data['sensor_value']
            
            # Проверка диапазона (зависит от стадии)
            if 0 <= temp_value <= 5:
                delta_color = "normal"
                delta_text = "✅ В норме"
            elif 43 <= temp_value <= 47:
                delta_color = "normal"
                delta_text = "✅ Сушка"
            else:
                delta_color = "off"
                delta_text = "⚠️ Проверить"
            
            st.metric(
                "🌡️ Температура",
                f"{temp_value:.1f} °C",
                delta=delta_text,
                delta_color=delta_color
            )
        else:
            st.metric("🌡️ Температура", "—")
    
    with col2:
        if 'humidity' in latest_values:
            hum_data = latest_values['humidity']
            hum_value = hum_data['sensor_value']
            st.metric(
                "💧 Влажность",
                f"{hum_value:.1f}%",
                delta="Камера"
            )
        else:
            st.metric("💧 Влажность", "—")
    
    with col3:
        if 'ph' in latest_values:
            ph_data = latest_values['ph']
            ph_value = ph_data['sensor_value']
            
            # Проверка pH диапазона (5.1-5.6)
            if 5.1 <= ph_value <= 5.6:
                delta_color = "normal"
                delta_text = "✅ Оптимально"
            else:
                delta_color = "inverse"
                delta_text = "⚠️ Вне нормы"
            
            st.metric(
                "🧪 pH",
                f"{ph_value:.2f}",
                delta=delta_text,
                delta_color=delta_color
            )
        else:
            st.metric("🧪 pH", "—")
    
    with col4:
        if 'water_activity' in latest_values:
            aw_data = latest_values['water_activity']
            aw_value = aw_data['sensor_value']
            
            # Проверка Aw диапазона (0.88-0.90)
            if 0.88 <= aw_value <= 0.90:
                delta_color = "normal"
                delta_text = "✅ Оптимально"
            else:
                delta_color = "off"
                delta_text = "⚠️ Проверить"
            
            st.metric(
                "💦 Активность воды (Aw)",
                f"{aw_value:.3f}",
                delta=delta_text,
                delta_color=delta_color
            )
        else:
            st.metric("💦 Aw", "—")
    
    st.markdown("---")
    
    # === ДОПОЛНИТЕЛЬНЫЕ ПОКАЗАТЕЛИ ===
    col_extra1, col_extra2, col_extra3, col_extra4 = st.columns(4)
    
    with col_extra1:
        if 'weight' in latest_values:
            weight_data = latest_values['weight']
            weight_value = weight_data['sensor_value']
            st.metric("⚖️ Масса", f"{weight_value:.0f} г")
        else:
            st.metric("⚖️ Масса", "—")
    
    with col_extra2:
        if 'orp' in latest_values:
            orp_data = latest_values['orp']
            orp_value = orp_data['sensor_value']
            st.metric("⚡ ORP", f"{orp_value:.0f} mV")
        else:
            st.metric("⚡ ORP", "—")
    
    with col_extra3:
        if 'pressure' in latest_values:
            pressure_data = latest_values['pressure']
            pressure_value = pressure_data['sensor_value']
            st.metric("🔧 Давление", f"{pressure_value:.2f} МПа")
        else:
            st.metric("🔧 Давление", "—")
    
    with col_extra4:
        if 'air_flow' in latest_values:
            flow_data = latest_values['air_flow']
            flow_value = flow_data['sensor_value']
            st.metric("🌬️ Поток воздуха", f"{flow_value:.2f} м/с")
        else:
            st.metric("🌬️ Поток", "—")
    
    st.markdown("---")
    
    # === ГРАФИКИ В РЕАЛЬНОМ ВРЕМЕНИ ===
    st.subheader("📈 Динамика показателей")
    
    # Табы для разных групп датчиков
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌡️ Температура и Влажность",
        "🧪 pH и Aw",
        "⚖️ Масса и Давление",
        "⚡ ORP и Поток воздуха"
    ])
    
    with tab1:
        # График температуры и влажности
        fig1 = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Температура (°C)", "Влажность (%)"),
            vertical_spacing=0.15
        )
        
        # Температура
        temp_df = df[df['sensor_type'] == 'temperature'].sort_values('time')
        if not temp_df.empty:
            for location in temp_df['sensor_location'].unique():
                loc_df = temp_df[temp_df['sensor_location'] == location]
                fig1.add_trace(
                    go.Scatter(
                        x=loc_df['time'],
                        y=loc_df['sensor_value'],
                        mode='lines+markers',
                        name=f"Темп. ({location})",
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )
        
        # Влажность
        hum_df = df[df['sensor_type'] == 'humidity'].sort_values('time')
        if not hum_df.empty:
            fig1.add_trace(
                go.Scatter(
                    x=hum_df['time'],
                    y=hum_df['sensor_value'],
                    mode='lines+markers',
                    name="Влажность",
                    line=dict(color='#1f77b4', width=2)
                ),
                row=2, col=1
            )
        
        fig1.update_xaxes(title_text="Время", row=2, col=1)
        fig1.update_yaxes(title_text="°C", row=1, col=1)
        fig1.update_yaxes(title_text="%", row=2, col=1)
        fig1.update_layout(height=600, hovermode='x unified', template='plotly_white')
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        # График pH и Aw
        fig2 = make_subplots(
            rows=2, cols=1,
            subplot_titles=("pH", "Активность воды (Aw)"),
            vertical_spacing=0.15
        )
        
        # pH
        ph_df = df[df['sensor_type'] == 'ph'].sort_values('time')
        if not ph_df.empty:
            for location in ph_df['sensor_location'].unique():
                loc_df = ph_df[ph_df['sensor_location'] == location]
                fig2.add_trace(
                    go.Scatter(
                        x=loc_df['time'],
                        y=loc_df['sensor_value'],
                        mode='lines+markers',
                        name=f"pH ({location})",
                        line=dict(width=2)
                    ),
                    row=1, col=1
                )
            
            # Целевой диапазон pH (5.1-5.6)
            fig2.add_hrect(
                y0=5.1, y1=5.6,
                fillcolor="green", opacity=0.15,
                layer="below", line_width=0,
                row=1, col=1
            )
        
        # Aw
        aw_df = df[df['sensor_type'] == 'water_activity'].sort_values('time')
        if not aw_df.empty:
            fig2.add_trace(
                go.Scatter(
                    x=aw_df['time'],
                    y=aw_df['sensor_value'],
                    mode='lines+markers',
                    name="Aw",
                    line=dict(color='#ff7f0e', width=2)
                ),
                row=2, col=1
            )
            
            # Целевой диапазон Aw (0.88-0.90)
            fig2.add_hrect(
                y0=0.88, y1=0.90,
                fillcolor="green", opacity=0.15,
                layer="below", line_width=0,
                row=2, col=1
            )
        
        fig2.update_xaxes(title_text="Время", row=2, col=1)
        fig2.update_yaxes(title_text="pH", row=1, col=1)
        fig2.update_yaxes(title_text="Aw", row=2, col=1)
        fig2.update_layout(height=600, hovermode='x unified', template='plotly_white')
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        # График массы и давления
        fig3 = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Масса продукта (г)", "Давление (МПа)"),
            vertical_spacing=0.15
        )
        
        # Масса
        weight_df = df[df['sensor_type'] == 'weight'].sort_values('time')
        if not weight_df.empty:
            fig3.add_trace(
                go.Scatter(
                    x=weight_df['time'],
                    y=weight_df['sensor_value'],
                    mode='lines+markers',
                    name="Масса",
                    line=dict(color='#2ca02c', width=2),
                    fill='tozeroy'
                ),
                row=1, col=1
            )
        
        # Давление
        pressure_df = df[df['sensor_type'] == 'pressure'].sort_values('time')
        if not pressure_df.empty:
            fig3.add_trace(
                go.Scatter(
                    x=pressure_df['time'],
                    y=pressure_df['sensor_value'],
                    mode='lines+markers',
                    name="Давление",
                    line=dict(color='#d62728', width=2)
                ),
                row=2, col=1
            )
        
        fig3.update_xaxes(title_text="Время", row=2, col=1)
        fig3.update_yaxes(title_text="г", row=1, col=1)
        fig3.update_yaxes(title_text="МПа", row=2, col=1)
        fig3.update_layout(height=600, hovermode='x unified', template='plotly_white')
        
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab4:
        # График ORP и потока воздуха
        fig4 = make_subplots(
            rows=2, cols=1,
            subplot_titles=("ORP (mV)", "Поток воздуха (м/с)"),
            vertical_spacing=0.15
        )
        
        # ORP
        orp_df = df[df['sensor_type'] == 'orp'].sort_values('time')
        if not orp_df.empty:
            fig4.add_trace(
                go.Scatter(
                    x=orp_df['time'],
                    y=orp_df['sensor_value'],
                    mode='lines+markers',
                    name="ORP",
                    line=dict(color='#9467bd', width=2)
                ),
                row=1, col=1
            )
        
        # Поток воздуха
        flow_df = df[df['sensor_type'] == 'air_flow'].sort_values('time')
        if not flow_df.empty:
            fig4.add_trace(
                go.Scatter(
                    x=flow_df['time'],
                    y=flow_df['sensor_value'],
                    mode='lines+markers',
                    name="Поток воздуха",
                    line=dict(color='#8c564b', width=2)
                ),
                row=2, col=1
            )
        
        fig4.update_xaxes(title_text="Время", row=2, col=1)
        fig4.update_yaxes(title_text="mV", row=1, col=1)
        fig4.update_yaxes(title_text="м/с", row=2, col=1)
        fig4.update_layout(height=600, hovermode='x unified', template='plotly_white')
        
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("---")
    
    # === УПРАВЛЕНИЕ АКТУАТОРАМИ ===
    st.subheader("🎛️ Управление процессом")
    
    st.info("💡 Отправка команд управления через MQTT → Актуаторы → БД")
    
    with st.expander("⚙️ Панель управления актуаторами", expanded=False):
        actuator_col1, actuator_col2 = st.columns(2)
        
        with actuator_col1:
            st.markdown("### Температура и влажность")
            
            temp_set = st.slider("🌡️ Установить температуру (°C)", 0, 85, 45)
            if st.button("Применить температуру"):
                if send_actuator_command(batch_id, "T_set", temp_set, "streamlit_user"):
                    st.success(f"✅ Команда отправлена: T_set = {temp_set}°C")
                else:
                    st.error("❌ Ошибка отправки команды")
            
            rh_set = st.slider("💧 Установить влажность (%)", 30, 90, 60)
            if st.button("Применить влажность"):
                if send_actuator_command(batch_id, "RH_env", rh_set, "streamlit_user"):
                    st.success(f"✅ Команда отправлена: RH_env = {rh_set}%")
                else:
                    st.error("❌ Ошибка отправки команды")
        
        with actuator_col2:
            st.markdown("### Давление и поток")
            
            pressure_set = st.slider("🔧 Давление прессования (МПа)", 0.5, 2.0, 1.25, 0.05)
            if st.button("Применить давление"):
                if send_actuator_command(batch_id, "P_press", pressure_set, "streamlit_user"):
                    st.success(f"✅ Команда отправлена: P_press = {pressure_set} МПа")
                else:
                    st.error("❌ Ошибка отправки команды")
            
            flow_set = st.slider("🌬️ Скорость воздуха (м/с)", 0.1, 1.0, 0.5, 0.1)
            if st.button("Применить скорость"):
                if send_actuator_command(batch_id, "v_set", flow_set, "streamlit_user"):
                    st.success(f"✅ Команда отправлена: v_set = {flow_set} м/с")
                else:
                    st.error("❌ Ошибка отправки команды")
    
    st.markdown("---")
    
    # === ТАБЛИЦА СЫРЫХ ДАННЫХ ===
    with st.expander("📋 Сырые данные датчиков", expanded=False):
        # Форматирование таблицы
        display_df = df.copy()
        display_df['time'] = display_df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df = display_df.sort_values('time', ascending=False)
        
        # Отображение
        st.dataframe(
            display_df[['time', 'sensor_type', 'sensor_location', 'sensor_value', 'sensor_unit']],
            use_container_width=True,
            hide_index=True
        )
        
        # Экспорт
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Скачать данные (CSV)",
            data=csv,
            file_name=f"iot_data_batch_{batch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # === АВТООБНОВЛЕНИЕ ===
    if auto_refresh and refresh_interval:
        st.caption(f"🔄 Автообновление через {refresh_interval} сек...")
        time.sleep(refresh_interval)
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)