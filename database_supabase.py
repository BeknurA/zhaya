import os
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import json


# =================================================================
# === КОНФИГУРАЦИЯ SUPABASE ===
# =================================================================

def get_supabase_config():
    """Получает конфигурацию Supabase"""
    try:
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            return {
                'url': st.secrets['supabase']['url'],
                'key': st.secrets['supabase']['key'],
                'db_url': st.secrets['supabase']['db_url']
            }
        else:
            return {
                'url': os.getenv('SUPABASE_URL'),
                'key': os.getenv('SUPABASE_KEY'),
                'db_url': os.getenv('SUPABASE_DB_URL')
            }
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации Supabase: {e}")
        return None


@st.cache_resource
def init_supabase():
    """Инициализирует клиент Supabase с проверкой"""
    config = get_supabase_config()
    if not config or not all(config.values()):
        st.error("⚠️ Конфигурация Supabase не найдена!")
        return None

    try:
        supabase: Client = create_client(config['url'], config['key'])
        # Проверка подключения
        response = supabase.table('production_batches').select('count', count='exact').limit(1).execute()
        return supabase
    except Exception as e:
        st.error(f"❌ Ошибка подключения к Supabase: {e}")
        return None


# =================================================================
# === КЭШИРОВАНИЕ С АВТОМАТИЧЕСКИМ УДАЛЕНИЕМ ===
# =================================================================

def get_cache_key(*args) -> str:
    """Генерирует ключ кэша из аргументов"""
    key_str = "_".join(str(arg) for arg in args)
    return hashlib.md5(key_str.encode()).hexdigest()


@st.cache_data(ttl=300)  # 5 минут
def fetch_production_batches_cached(limit: int = 100):
    """Кэшированное получение партий"""
    return fetch_production_batches(limit)


@st.cache_data(ttl=180)  # 3 минуты
def fetch_lab_measurements_cached(batch_id: int = None):
    """Кэшированное получение измерений"""
    return fetch_lab_measurements(batch_id)


@st.cache_data(ttl=600)  # 10 минут для отчетов
def fetch_dashboard_config_cached():
    """Кэшированная конфигурация дашборда"""
    return fetch_dashboard_config()


@st.cache_data(ttl=600)
def fetch_reports_config_cached():
    """Кэшированная конфигурация отчетов"""
    return fetch_reports_config()


def clear_all_caches():
    """Очистка всех кэшей"""
    st.cache_data.clear()
    st.cache_resource.clear()


# =================================================================
# === ПРОИЗВОДСТВЕННЫЕ ПАРТИИ ===
# =================================================================
def fetch_activity_logs(limit: int = 100):
    """Получает логи активности пользователей"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()

    try:
        response = supabase.table('activity_logs') \
            .select('*, users(full_name, username)') \
            .order('timestamp', desc=True) \
            .limit(limit) \
            .execute()

        if response.data:
            df = pd.DataFrame(response.data)
            # Разворачиваем данные пользователя из словаря в отдельные колонки
            if 'users' in df.columns:
                user_df = pd.json_normalize(df['users'])
                user_df.rename(columns={'full_name': 'full_name', 'username': 'username'}, inplace=True)
                df = df.drop(columns=['users']).join(user_df)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения логов активности: {e}")
        return pd.DataFrame()


def create_production_batch(product_type: str, target_concentration: float,
                            initial_weight: float, user_id: str = None) -> Optional[Dict]:
    """Создает новую производственную партию с валидацией"""
    supabase = init_supabase()
    if not supabase:
        return None

    # Валидация данных
    if target_concentration < 0 or target_concentration > 15:
        st.error("Концентрация должна быть от 0 до 15%")
        return None

    if initial_weight <= 0:
        st.error("Вес должен быть положительным числом")
        return None

    try:
        data = {
            'product_type': product_type,
            'target_sea_buckthorn_concentration': target_concentration,
            'initial_weight': initial_weight
        }
        response = supabase.table('production_batches').insert(data).execute()

        # Логирование
        if response.data and user_id:
            log_user_action(user_id, "create_batch", f"Создана партия ID: {response.data[0]['batch_id']}")

        # Очистка кэша
        clear_all_caches()

        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Ошибка создания партии: {e}")
        return None


def fetch_production_batches(limit: int = 100) -> pd.DataFrame:
    """Получает список производственных партий"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()

    try:
        response = supabase.table('production_batches') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения партий: {e}")
        return pd.DataFrame()


def fetch_iot_sensor_data(batch_id: int = None, limit: int = 1000):
    """Получает данные IoT сенсоров"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()

    try:
        query = supabase.table('iot_sensor_data') \
            .select('*') \
            .order('time', desc=True) \
            .limit(limit)

        if batch_id:
            query = query.eq('batch_id', batch_id)

        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения данных сенсоров: {e}")
        return pd.DataFrame()
def update_batch_weight(batch_id: int, final_weight: float, user_id: str = None) -> bool:
    """Обновляет финальный вес партии"""
    supabase = init_supabase()
    if not supabase:
        return False

    if final_weight <= 0:
        st.error("Вес должен быть положительным")
        return False

    try:
        response = supabase.table('production_batches') \
            .update({'final_weight': final_weight, 'end_time': datetime.utcnow().isoformat()}) \
            .eq('batch_id', batch_id) \
            .execute()

        if user_id:
            log_user_action(user_id, "update_batch", f"Обновлен вес партии {batch_id}: {final_weight} кг")

        clear_all_caches()
        return bool(response.data)
    except Exception as e:
        st.error(f"Ошибка обновления: {e}")
        return False


# =================================================================
# === ЛАБОРАТОРНЫЕ ИЗМЕРЕНИЯ ===
# =================================================================

def add_lab_measurement(batch_id: int, parameter_name: str, parameter_value: float,
                        parameter_unit: str, lab_technician: str = None,
                        notes: str = None, user_id: str = None) -> bool:
    """Добавляет лабораторное измерение с валидацией"""
    supabase = init_supabase()
    if not supabase:
        return False

    # Валидация параметра
    valid_params = get_parameter_options()
    if parameter_name not in valid_params:
        st.error(f"Неверный параметр. Допустимые: {', '.join(valid_params)}")
        return False

    # Валидация значения
    if parameter_value < 0:
        st.warning("Отрицательное значение параметра")

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

        if user_id:
            log_user_action(user_id, "add_measurement",
                            f"Добавлено измерение {parameter_name} для партии {batch_id}")

        clear_all_caches()
        return bool(response.data)
    except Exception as e:
        st.error(f"Ошибка добавления измерения: {e}")
        return False


def fetch_lab_measurements(batch_id: int = None) -> pd.DataFrame:
    """Получает лабораторные измерения"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()

    try:
        query = supabase.table('lab_measurements') \
            .select('*, production_batches(product_type, batch_id)') \
            .order('measurement_time', desc=True)

        if batch_id:
            query = query.eq('batch_id', batch_id)

        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения измерений: {e}")
        return pd.DataFrame()


# =================================================================
# === ДАШБОРДЫ И ОТЧЕТЫ ИЗ БД ===
# =================================================================

def fetch_dashboard_config() -> Optional[Dict]:
    """Получает конфигурацию дашборда из БД"""
    supabase = init_supabase()
    if not supabase:
        return None

    try:
        # Предполагаем наличие таблицы dashboard_config
        response = supabase.table('dashboard_config') \
            .select('*') \
            .eq('is_active', True) \
            .execute()

        if response.data:
            return response.data[0]

        # Если нет в БД, возвращаем дефолтную конфигурацию
        return get_default_dashboard_config()
    except:
        return get_default_dashboard_config()


def get_default_dashboard_config() -> Dict:
    """Дефолтная конфигурация дашборда"""
    return {
        "title": "Производственный Dashboard",
        "kpis": [
            {"name": "production_today", "label": "Произведено сегодня", "unit": "кг"},
            {"name": "yield_pct", "label": "Выход продукции", "unit": "%"},
            {"name": "avg_ph", "label": "Средний pH", "unit": ""},
            {"name": "active_batches", "label": "Активных партий", "unit": ""},
            {"name": "efficiency", "label": "OEE эффективность", "unit": "%"}
        ],
        "charts": [
            {"type": "production_week", "title": "Динамика производства"},
            {"type": "ph_stages", "title": "Мониторинг pH"},
            {"type": "quality_pie", "title": "Распределение по качеству"}
        ]
    }


def fetch_reports_config() -> List[Dict]:
    """Получает конфигурацию отчетов из БД"""
    supabase = init_supabase()
    if not supabase:
        return get_default_reports_config()

    try:
        response = supabase.table('reports_config') \
            .select('*') \
            .eq('is_active', True) \
            .order('display_order') \
            .execute()

        if response.data:
            return response.data

        return get_default_reports_config()
    except:
        return get_default_reports_config()


def get_default_reports_config() -> List[Dict]:
    """Дефолтная конфигурация отчетов"""
    return [
        {
            "report_id": "production",
            "name": "Производственный отчет",
            "description": "Детальный анализ производства за период",
            "icon": "📅",
            "sections": ["kpi", "production_table", "charts"]
        },
        {
            "report_id": "quality",
            "name": "Анализ качества",
            "description": "Контроль качественных показателей",
            "icon": "📈",
            "sections": ["quality_metrics", "ph_analysis", "oxidation"]
        },
        {
            "report_id": "economic",
            "name": "Экономические показатели",
            "description": "Финансовый анализ производства",
            "icon": "💰",
            "sections": ["revenue", "costs", "profitability"]
        }
    ]


def save_dashboard_config(config: Dict, user_id: str) -> bool:
    """Сохраняет конфигурацию дашборда"""
    supabase = init_supabase()
    if not supabase:
        return False

    try:
        # Деактивируем старые конфигурации
        supabase.table('dashboard_config').update({'is_active': False}).execute()

        # Сохраняем новую
        config['is_active'] = True
        config['updated_by'] = user_id
        config['updated_at'] = datetime.utcnow().isoformat()

        response = supabase.table('dashboard_config').insert(config).execute()

        log_user_action(user_id, "update_dashboard_config", "Обновлена конфигурация дашборда")
        clear_all_caches()

        return bool(response.data)
    except Exception as e:
        st.error(f"Ошибка сохранения конфигурации: {e}")
        return False


# =================================================================
# === ЛОГИРОВАНИЕ ДЕЙСТВИЙ ===
# =================================================================

def log_user_action(user_id: str, action: str, details: str = "", metadata: Dict = None):
    """Логирование действий пользователя"""
    supabase = init_supabase()
    if not supabase:
        return

    try:
        log_data = {
            'user_id': user_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }

        if metadata:
            log_data['metadata'] = json.dumps(metadata)

        supabase.table('activity_logs').insert(log_data).execute()
    except Exception as e:
        print(f"Ошибка логирования: {e}")


def fetch_activity_logs(user_id: str = None, limit: int = 100) -> pd.DataFrame:
    """Получает логи активности"""
    supabase = init_supabase()
    if not supabase:
        return pd.DataFrame()

    try:
        query = supabase.table('activity_logs') \
            .select('*') \
            .order('timestamp', desc=True) \
            .limit(limit)

        if user_id:
            query = query.eq('user_id', user_id)

        response = query.execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка получения логов: {e}")
        return pd.DataFrame()


# =================================================================
# === СТАТИСТИКА И АНАЛИТИКА ===
# =================================================================

@st.cache_data(ttl=300)
def get_production_statistics(date_from: datetime, date_to: datetime) -> Dict:
    """Получает статистику производства за период"""
    supabase = init_supabase()
    if not supabase:
        return {}

    try:
        # Партии за период
        batches = supabase.table('production_batches') \
            .select('*') \
            .gte('start_time', date_from.isoformat()) \
            .lte('start_time', date_to.isoformat()) \
            .execute()

        df = pd.DataFrame(batches.data) if batches.data else pd.DataFrame()

        if df.empty:
            return {}

        stats = {
            'total_batches': len(df),
            'total_weight': df['initial_weight'].sum(),
            'avg_concentration': df['target_sea_buckthorn_concentration'].mean(),
            'product_types': df['product_type'].value_counts().to_dict()
        }

        return stats
    except Exception as e:
        st.error(f"Ошибка получения статистики: {e}")
        return {}


def get_batch_details(batch_id: int):
    """Получает детальную информацию о партии"""
    supabase = init_supabase()
    if not supabase:
        return None

    try:
        # Основная информация о партии
        batch_response = supabase.table('production_batches') \
            .select('*') \
            .eq('batch_id', batch_id) \
            .execute()

        if not batch_response.data:
            return None

        batch_data = batch_response.data[0]

        # Лабораторные измерения
        lab_data = fetch_lab_measurements(batch_id)

        # Данные сенсоров
        sensor_data = fetch_iot_sensor_data(batch_id, limit=100)

        # Этапы производства
        stages_response = supabase.table('production_stages') \
            .select('*') \
            .eq('batch_id', batch_id) \
            .order('stage_order') \
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

def get_parameter_options() -> List[str]:
    """Возвращает список доступных параметров"""
    return [
        'W', 'S', 'pH', 'ORP', 'protein', 'fat', 'ash', 'C_L', 'C_a', 'C_b',
        'WBC', 'WRC', 'FBC', 'TBARS', 'peroxide_value', 'antioxidants',
        'beta_carotene', 'flavonoids', 'vitamin_c', 'vitamin_e', 'TAMC'
    ]


def get_product_types() -> List[str]:
    """Возвращает типы продуктов"""
    return ['Жая', 'Формованное мясо']


def validate_batch_data(data: Dict) -> tuple[bool, str]:
    """Валидация данных партии"""
    if 'product_type' not in data or data['product_type'] not in get_product_types():
        return False, "Неверный тип продукта"

    if data.get('target_sea_buckthorn_concentration', 0) > 15:
        return False, "Концентрация не может превышать 15%"

    if data.get('initial_weight', 0) <= 0:
        return False, "Вес должен быть положительным"

    return True, "OK"