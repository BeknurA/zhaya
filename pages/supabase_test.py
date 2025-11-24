import streamlit as st
import pandas as pd
from database_supabase import (
    init_supabase,
    create_production_batch,
    fetch_production_batches,
    add_lab_measurement,
    fetch_lab_measurements,
    fetch_iot_sensor_data,
    get_parameter_options,
    get_product_types,
    get_batch_details
)


# =================================================================
# === ОСНОВНАЯ ФУНКЦИЯ СТРАНИЦЫ (ВСЁ ВНУТРИ НЕЁ!) ===
# =================================================================

def show_supabase_test():
    st.title("🔧 Тестирование подключения к Supabase")
    st.markdown("---")

    # ==============================================================
    # === 1. Тест подключения
    # ==============================================================

    st.header("🔌 Проверка подключения")

    if st.button("🔄 Проверить подключение к Supabase"):
        supabase = init_supabase()
        if supabase:
            st.success("✅ Подключение к Supabase успешно установлено!")

            try:
                batches_response = supabase.table('production_batches') \
                    .select('count', count='exact').limit(1).execute()
                batches_count = getattr(batches_response, "count", "N/A")

                lab_response = supabase.table('lab_measurements') \
                    .select('count', count='exact').limit(1).execute()
                lab_count = getattr(lab_response, "count", "N/A")

                st.info(f"""
                **Статистика базы данных:**
                - Производственные партии: {batches_count}
                - Лабораторные измерения: {lab_count}
                """)

            except Exception as e:
                st.warning(f"⚠️ Ошибка при запросе таблиц: {e}")

        else:
            st.error("❌ Не удалось подключиться к Supabase")

    st.markdown("---")

    # ==============================================================
    # === 2. Тест создания партии
    # ==============================================================

    st.header("🏭 Тест создания производственной партии")

    with st.form("create_batch_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            product_type = st.selectbox("Тип продукта", get_product_types())

        with col2:
            target_concentration = st.number_input(
                "Концентрация облепихи (%)",
                min_value=0.0, max_value=15.0, value=5.0, step=0.1
            )

        with col3:
            initial_weight = st.number_input(
                "Начальный вес (кг)",
                min_value=0.1, value=10.0, step=0.1
            )

        submit_batch = st.form_submit_button("📦 Создать тестовую партию")

        if submit_batch:
            with st.spinner("Создание партии..."):
                result = create_production_batch(
                    product_type=product_type,
                    target_concentration=target_concentration,
                    initial_weight=initial_weight
                )

                if result:
                    st.success(f"✅ Партия создана! ID: {result['batch_id']}")
                    st.json(result)
                else:
                    st.error("❌ Ошибка при создании партии")

    # ==============================================================
    # === 3. Тест получения данных
    # ==============================================================

    st.header("📊 Тест получения данных")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Получить все партии"):
            with st.spinner("Загрузка партий..."):
                batches_df = fetch_production_batches()

                if not batches_df.empty:
                    st.success(f"✅ Загружено {len(batches_df)} партий")

                    display_df = batches_df[['batch_id', 'product_type', 'initial_weight', 'start_time']].copy()
                    if 'start_time' in display_df.columns:
                        display_df['start_time'] = pd.to_datetime(display_df['start_time']).dt.strftime('%Y-%m-%d %H:%M')

                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("📭 Нет данных о производственных партиях")

    with col2:
        if st.button("🧪 Получить лабораторные измерения"):
            with st.spinner("Загрузка измерений..."):
                measurements_df = fetch_lab_measurements()

                if not measurements_df.empty:
                    st.success(f"✅ Загружено {len(measurements_df)} измерений")

                    if 'measurement_time' in measurements_df.columns:
                        measurements_df['measurement_time'] = pd.to_datetime(
                            measurements_df['measurement_time']
                        ).dt.strftime('%Y-%m-%d %H:%M')

                    st.dataframe(measurements_df.head(10), use_container_width=True)
                else:
                    st.info("📭 Нет данных о лабораторных измерениях")

    # ==============================================================
    # === 4. Тест добавления измерения
    # ==============================================================

    st.header("🔬 Тест добавления лабораторного измерения")

    batches_df = fetch_production_batches()
    if not batches_df.empty:
        batch_options = {
            row['batch_id']: f"ID {row['batch_id']} - {row['product_type']}"
            for _, row in batches_df.iterrows()
        }

        with st.form("add_measurement_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                selected_batch = st.selectbox(
                    "Выберите партию",
                    options=list(batch_options.keys()),
                    format_func=lambda x: batch_options[x]
                )
                parameter_name = st.selectbox("Параметр", get_parameter_options())

            with col2:
                parameter_value = st.number_input("Значение", value=0.0, step=0.1)
                parameter_unit = st.text_input("Единица измерения", value="g/100g")

            with col3:
                lab_technician = st.text_input("Лаборант", value="Тестовый лаборант")
                notes = st.text_area("Заметки", value="Тестовое измерение")

            submit_measurement = st.form_submit_button("➕ Добавить измерение")

            if submit_measurement:
                with st.spinner("Добавление измерения..."):
                    success = add_lab_measurement(
                        batch_id=selected_batch,
                        parameter_name=parameter_name,
                        parameter_value=parameter_value,
                        parameter_unit=parameter_unit,
                        lab_technician=lab_technician,
                        notes=notes
                    )

                    if success:
                        st.success("✅ Измерение успешно добавлено!")
                    else:
                        st.error("❌ Ошибка при добавлении измерения")
    else:
        st.warning("⚠️ Сначала создайте производственную партию")

    # ==============================================================
    # === 5. Детали партии
    # ==============================================================

    st.header("📋 Тест детальной информации о партии")

    if not batches_df.empty:
        selected_batch_detail = st.selectbox(
            "Выберите партию для просмотра",
            options=batches_df['batch_id'].tolist()
        )

        if st.button("🔍 Загрузить детали партии"):
            with st.spinner("Загрузка деталей..."):
                batch_details = get_batch_details(selected_batch_detail)

                if batch_details:
                    st.success("Детали загружены!")
                    st.json(batch_details)
                else:
                    st.error("❌ Не удалось загрузить детали партии")

    st.markdown("---")
    st.info("""
    Эта страница используется для тестирования Supabase.
    Все операции происходят с реальной базой данных.
    """)
