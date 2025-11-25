# Meat_Digitalization/pages/history_db.py
import streamlit as st
import pandas as pd
import plotly.express as px
from ui import get_text, df_to_download_link
from database_supabase import (
    fetch_lab_measurements,
    add_lab_measurement,
    fetch_production_batches,
    get_parameter_options
)


def show_history_db(lang_choice):
    st.markdown("<div class='fade-in'>", unsafe_allow_html=True)

    st.title("🧪 Лабораторный Журнал")

    # --- Форма добавления нового измерения ---
    st.subheader("➕ Добавить Новое Измерение")

    batches = fetch_production_batches()
    if batches.empty:
        st.warning("Нет доступных производственных партий. Сначала создайте партию.")
        batch_options = []
    else:
        batch_options = {f"{row['product_type']} (ID: {row['batch_id']})": row['batch_id'] for index, row in
                         batches.iterrows()}

    parameter_options = get_parameter_options()
    user_full_name = st.session_state.get("user", {}).get("full_name", "")

    with st.form(key='add_measurement_form', clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_batch_label = st.selectbox("Производственная партия", options=list(batch_options.keys()))
            parameter_name = st.selectbox("Параметр", options=parameter_options)
            parameter_value = st.number_input("Значение", format="%.3f")

        with col2:
            parameter_unit = st.text_input("Единица измерения", value="N/A")
            lab_technician = st.text_input("Лаборант", value=user_full_name)
            notes = st.text_area("Заметки")

        submit_button = st.form_submit_button(label='Сохранить Измерение ✅')

        if submit_button:
            if not selected_batch_label:
                st.error("Пожалуйста, выберите производственную партию.")
            else:
                batch_id = batch_options[selected_batch_label]
                success = add_lab_measurement(
                    batch_id=batch_id,
                    parameter_name=parameter_name,
                    parameter_value=parameter_value,
                    parameter_unit=parameter_unit,
                    lab_technician=lab_technician,
                    notes=notes
                )
                if success:
                    st.success(f"Измерение для партии ID {batch_id} успешно добавлено.")
                    st.rerun()
                else:
                    st.error("Не удалось добавить измерение.")

    st.markdown("---")

    # --- Отображение истории измерений ---
    st.header(get_text("db_title", lang_choice))
    st.markdown(f"### {get_text('db_desc', lang_choice)}")

    df_lab_measurements = fetch_lab_measurements()

    if df_lab_measurements.empty:
        st.info(get_text("history_empty", lang_choice))
    else:
        df_db = df_lab_measurements.copy()
        if 'production_batches' in df_db.columns and not df_db['production_batches'].isnull().all():
            try:
                batches_df = pd.json_normalize(df_db['production_batches'].dropna())
                batches_df = batches_df.add_prefix('batch_')
                df_db = df_db.join(batches_df)
                df_db.drop(columns=['production_batches'], inplace=True)

                if 'batch_product_type' in df_db.columns and 'batch_batch_id' in df_db.columns:
                    df_db['sample_name'] = df_db['batch_product_type'].astype(str) + ' - ' + df_db[
                        'batch_batch_id'].astype(str)
                else:
                    df_db['sample_name'] = 'Unknown Batch'
            except Exception as e:
                st.warning(f"Could not process batch details: {e}")
                df_db['sample_name'] = 'Processing Error'
        else:
            df_db['sample_name'] = 'Unknown Batch'

        df_db = df_db.rename(columns={'measurement_time': 'created_at'})

        df_ph = df_db[df_db['parameter_name'] == 'pH'].copy()

        st.subheader(f"{get_text('total_records', lang_choice)} {len(df_db)}")
        st.dataframe(df_db, use_container_width=True)

        if not df_ph.empty:
            fig_db = px.line(
                df_ph.sort_values('created_at'),
                x='created_at',
                y='parameter_value',
                color='sample_name',
                title=get_text("ph_over_time", lang_choice),
                template='plotly_dark'
            )
            st.plotly_chart(fig_db, use_container_width=True)
        else:
            st.info("Нет данных pH для построения графика.")

        st.markdown("---")
        st.markdown(df_to_download_link(df_db, "measurements_export.csv", get_text("export_all", lang_choice)),
                    unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
