import os
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict

# =================================================================
# === КОНФИГУРАЦИЯ SUPABASE ===
# =================================================================

# Безопасное хранение конфигурации - через environment variables или st.secrets
def get_supabase_config():
    """Получает конфигурацию Supabase из переменных окружения или secrets"""
    try:
        # Вариант 1: Используем st.secrets (рекомендуется для Streamlit)
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            return {
                'url': st.secrets['supabase']['url'],
                'key': st.secrets['supabase']['key'],
                'db_url': st.secrets['supabase']['db_url']
            }
        # Вариант 2: Используем переменные окружения
        else:
            return {
                'url': os.getenv('SUPABASE_URL'),
                'key': os.getenv('SUPABASE_KEY'), 
                'db_url': os.getenv('SUPABASE_DB_URL')
            }
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации Supabase: {e}")
        return None

# =================================================================
# === КЛИЕНТ SUPABASE ===
# =================================================================

@st.cache_resource
def init_supabase():
    """Инициализирует и возвращает клиент Supabase"""
    config = get_supabase_config()
    if not config or not all(config.values()):
        st.error("""
        ⚠️ Конфигурация Supabase не найдена!
        
        Добавьте в файл `.streamlit/secrets.toml`:
        ```toml
        [supabase]
        url = "https://ваш-проект.supabase.co"
        key = "ваш-anon-key"
        db_url = "postgresql://postgres:ваш-пароль@db.ваш-проект.supabase.co:5432/postgres"
        ```
        """)
        return None
    
    try:
        supabase: Client = create_client(config['url'], config['key'])
        # Проверяем подключение
        response = supabase.table('production_batches').select('count', count='exact').limit(1).execute()
        st.success("✅ Подключение к Supabase установлено")
        return supabase
    except Exception as e:
        st.error(f"❌ Ошибка подключения к Supabase: {e}")
        return None

# =================================================================
# === ОСНОВНЫЕ ФУНКЦИИ ДЛЯ НОВОЙ БД ===
# =================================================================

def create_production_batch(product_type: str, target_concentration: float, initial_weight: float, user_id: str):
    """
    Создает новую производственную партию с валидацией данных.
    Также логирует это действие.
    """
    # --- Валидация данных ---
    if not all([product_type, target_concentration is not None, initial_weight is not None]):
        st.error("Все поля должны быть заполнены.")
        return None
    if initial_weight <= 0:
        st.error("Начальный вес должен быть положительным числом.")
        return None
    if not (0 <= target_concentration <= 15):
        st.error("Концентрация облепихи должна быть в диапазоне от 0 до 15%.")
        return None

    supabase = init_supabase()
    if not supabase:
        return None
    
    try:
        data = {
            'product_type': product_type,
            'target_sea_buckthorn_concentration': target_concentration,
            'initial_weight': initial_weight
        }
        response = supabase.table('production_batches').insert(data).execute()

        if response.data:
            batch_info = response.data[0]
            # Логируем успешное создание
            log_details = {
                "batch_id": batch_info.get('batch_id'),
                "product_type": product_type,
                "initial_weight": initial_weight
            }
            log_activity(user_id, "create_batch", details=log_details)
            return batch_info
        return None

    except Exception as e:
        st.error(f"Ошибка создания партии: {e}")
        log_activity(user_id, "create_batch_failed", details={"error": str(e)})
        return None

@st.cache_data(ttl=60)
def fetch_production_batches(limit: int = 100):
    """Получает список производственных партий"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table('production_batches')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения партий: {e}")
        return pd.DataFrame()

def add_lab_measurement(batch_id: int, parameter_name: str, parameter_value: float, 
                       parameter_unit: str, lab_technician: str = None, notes: str = None):
    """Добавляет лабораторное измерение"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        data = {
            'batch_id': batch_id,
            'parameter_name': parameter_name,
            'parameter_value': parameter_value,
            'parameter_unit': parameter_unit,
            'lab_technician': lab_technician,
            'notes': notes
        }
        response = supabase.table('lab_measurements').insert(data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Ошибка добавления измерения: {e}")
        return False

@st.cache_data(ttl=60)
def fetch_lab_measurements(batch_id: int = None):
    """Получает лабораторные измерения (все или для конкретной партии)"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()
    
    try:
        query = supabase.table('lab_measurements')\
            .select('*, production_batches(product_type, batch_id)')\
            .order('measurement_time', desc=True)
        
        if batch_id:
            query = query.eq('batch_id', batch_id)
        
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения измерений: {e}")
        return pd.DataFrame()

def fetch_iot_sensor_data(batch_id: int = None, limit: int = 1000):
    """Получает данные IoT сенсоров"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()
    
    try:
        query = supabase.table('iot_sensor_data')\
            .select('*')\
            .order('time', desc=True)\
            .limit(limit)
        
        if batch_id:
            query = query.eq('batch_id', batch_id)
        
        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения данных сенсоров: {e}")
        return pd.DataFrame()

# =================================================================
# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ===
# =================================================================

def get_batch_details(batch_id: int):
    """Получает детальную информацию о партии"""
    supabase = init_supabase()
    if not supabase:
        return None
    
    try:
        # Основная информация о партии
        batch_response = supabase.table('production_batches')\
            .select('*')\
            .eq('batch_id', batch_id)\
            .execute()
        
        if not batch_response.data:
            return None
        
        batch_data = batch_response.data[0]
        
        # Лабораторные измерения
        lab_data = fetch_lab_measurements(batch_id)
        
        # Данные сенсоров
        sensor_data = fetch_iot_sensor_data(batch_id, limit=100)
        
        # Этапы производства
        stages_response = supabase.table('production_stages')\
            .select('*')\
            .eq('batch_id', batch_id)\
            .order('stage_order')\
            .execute()
        
        stages_data = pd.DataFrame(stages_response.data) if stages_response.data else pd.DataFrame()
        
        return {
            'batch_info': batch_data,
            'lab_measurements': lab_data,
            'sensor_data': sensor_data,
            'production_stages': stages_data
        }
    except Exception as e:
        st.error(f"Ошибка получения деталей партии: {e}")
        return None

# =================================================================
# === УТИЛИТЫ ===
# =================================================================

def get_parameter_options():
    """Возвращает доступные параметры для лабораторных измерений"""
    return [
        'W', 'S', 'pH', 'ORP', 'protein', 'fat', 'ash', 'C_L', 'C_a', 'C_b',
        'WBC', 'WRC', 'FBC', 'TBARS', 'peroxide_value', 'antioxidants',
        'beta_carotene', 'flavonoids', 'vitamin_c', 'vitamin_e', 'TAMC'
    ]

def get_sensor_types():
    """Возвращает доступные типы сенсоров"""
    return [
        'temperature', 'humidity', 'weight', 'water_activity', 
        'ph', 'orp', 'pressure', 'air_flow'
    ]

def get_product_types():
    """Возвращает доступные типы продуктов"""
    return ['Жая', 'Формованное мясо']

# =================================================================
# === НОВЫЕ ФУНКЦИИ ДЛЯ ДАШБОРДОВ И ОТЧЕТОВ ===
# =================================================================

@st.cache_data(ttl=300) # Кэширование на 5 минут
def fetch_dashboard_config(dashboard_id: int):
    """
    Получает конфигурацию дашборда, включая все связанные с ним отчеты.
    """
    supabase = init_supabase()
    if not supabase:
        return None, []

    try:
        # Получаем информацию о дашборде
        dashboard_response = supabase.table('dashboards').select('*').eq('dashboard_id', dashboard_id).single().execute()
        dashboard_data = dashboard_response.data

        if not dashboard_data:
            return None, []

        # Получаем связанные отчеты и их расположение
        reports_response = supabase.table('dashboard_reports')\
            .select('*, reports(*)')\
            .eq('dashboard_id', dashboard_id)\
            .execute()

        reports_data = reports_response.data

        return dashboard_data, reports_data

    except Exception as e:
        st.error(f"Ошибка при загрузке конфигурации дашборда: {e}")
        return None, []

@st.cache_data(ttl=300)
def fetch_report_data(query: str):
    """
    Выполняет SQL-запрос отчета и возвращает данные в виде DataFrame.
    """
    supabase = init_supabase()
    if not supabase or not query:
        return pd.DataFrame()

    try:
        # Для выполнения произвольных запросов нам нужно использовать прямое подключение к БД,
        # так как Supabase Python client не поддерживает произвольные `SELECT`.
        # Мы будем использовать `psycopg2`, который должен быть установлен.
        import psycopg2

        config = get_supabase_config()
        db_url = config.get('db_url')

        if not db_url:
            st.error("DB URL не найден в конфигурации.")
            return pd.DataFrame()

        with psycopg2.connect(db_url) as conn:
            df = pd.read_sql_query(query, conn)

        return df

    except Exception as e:
        # Важно: Обрабатываем ошибки, чтобы вредоносный SQL не сломал приложение
        st.error(f"Ошибка выполнения запроса для отчета: {e}")
        return pd.DataFrame()