# 📊 Платформа «Жая» — Комплексная документация

## 🎯 Содержание

1. [Обзор системы](#обзор-системы)
2. [Архитектура](#архитектура)
3. [Диаграммы](#диаграммы)
4. [Установка и запуск](#установка-и-запуск)
5. [Структура проекта](#структура-проекта)
6. [Модули и функциональность](#модули-и-функциональность)
7. [API и интеграции](#api-и-интеграции)
8. [Безопасность](#безопасность)
9. [Мониторинг и IoT](#мониторинг-и-iot)
10. [Руководство разработчика](#руководство-разработчика)

---

## 🌟 Обзор системы

**Платформа «Жая»** — это комплексная цифровая система для управления производством мясных деликатесов с интегрированными возможностями:

- 🏭 **Управление производством** — полный цикл от приемки сырья до упаковки
- 📊 **Аналитика и прогнозирование** — ML-модели для предсказания качества
- 🔬 **Лабораторный контроль** — учет всех измерений (pH, влажность, Aw, ТБЧ)
- 📡 **IoT-мониторинг** — датчики температуры, влажности, pH в режиме реального времени
- 👥 **Многопользовательская система** — роли (оператор, аналитик, менеджер, администратор)
- 🌍 **Мультиязычность** — Русский, English, Қазақша

### Ключевые технологии

```
Frontend:  Streamlit + Plotly
Backend:   Python 3.9+
Database:  Supabase (PostgreSQL)
IoT:       MQTT (Eclipse Mosquitto)
ML:        scikit-learn, statsmodels
```

---

## 🏗️ Архитектура

### Общая архитектура системы

```mermaid
graph TB
    subgraph "Пользовательский интерфейс"
        UI[Streamlit Web App]
    end
    
    subgraph "Бизнес-логика"
        AUTH[Модуль аутентификации]
        PROD[Управление производством]
        LAB[Лабораторные измерения]
        ML[ML-модели прогнозирования]
        IOT[IoT-обработка данных]
        REPORTS[Генерация отчетов]
    end
    
    subgraph "Слой данных"
        DB[(Supabase PostgreSQL)]
        CACHE[Кэш Streamlit]
    end
    
    subgraph "IoT Infrastructure"
        MQTT[MQTT Broker]
        SENSORS[IoT Датчики]
        SIMULATOR[Симулятор]
    end
    
    UI --> AUTH
    UI --> PROD
    UI --> LAB
    UI --> ML
    UI --> IOT
    UI --> REPORTS
    
    AUTH --> DB
    PROD --> DB
    LAB --> DB
    ML --> DB
    IOT --> DB
    REPORTS --> DB
    
    PROD --> CACHE
    LAB --> CACHE
    
    SENSORS --> MQTT
    SIMULATOR --> MQTT
    MQTT --> IOT
    IOT --> DB
```

---

## 📐 Диаграммы

### 1. Sequence Diagram: Процесс аутентификации

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant Auth as auth.py
    participant Supabase as Supabase DB
    participant Session as Session State
    
    User->>UI: Ввод email + password
    UI->>Auth: authenticate_user(email, password)
    Auth->>Auth: hash_password(password)
    Auth->>Supabase: SELECT users WHERE email & password_hash
    
    alt Пользователь найден и активен
        Supabase-->>Auth: user_data
        Auth->>Supabase: INSERT INTO user_sessions (session_token)
        Auth->>Supabase: UPDATE users.last_login
        Auth->>Supabase: INSERT INTO activity_logs (login)
        Auth-->>UI: {authenticated: true, user_data, session_token}
        UI->>Session: st.session_state.user = user_data
        UI-->>User: ✅ Добро пожаловать!
    else Пользователь не найден / неактивен
        Supabase-->>Auth: []
        Auth->>Supabase: INSERT INTO activity_logs (failed_login)
        Auth-->>UI: {authenticated: false, error}
        UI-->>User: ❌ Неверный логин или пароль
    end
```

### 2. Sequence Diagram: IoT Data Flow

```mermaid
sequenceDiagram
    participant Simulator as mqtt_client.py
    participant Broker as MQTT Broker
    participant IoT as IoT Module
    participant DB as Supabase DB
    participant Dashboard as Dashboard UI
    
    loop Каждые 5 секунд
        Simulator->>Simulator: generate_sensor_data()
        Simulator->>Broker: PUBLISH zhaya/sensors/data (JSON)
        Broker->>IoT: SUBSCRIBE message received
        IoT->>IoT: parse_sensor_data()
        IoT->>DB: INSERT INTO iot_sensor_data
        DB-->>IoT: ✅ Success
    end
    
    Dashboard->>DB: fetch_iot_sensor_data(batch_id, limit)
    DB-->>Dashboard: sensor_data[]
    Dashboard->>Dashboard: render_charts()
    Dashboard-->>User: 📊 Real-time graphs
    
    User->>Dashboard: Отправить команду актуатору
    Dashboard->>Broker: PUBLISH zhaya/actuators/commands
    Broker->>Simulator: Команда получена
    Simulator->>DB: INSERT INTO actuator_logs
```

### 3. Class Diagram: Основные модули

```mermaid
classDiagram
    class User {
        +str user_id
        +str email
        +str password_hash
        +str full_name
        +str role
        +str department
        +bool is_active
        +datetime created_at
        +datetime last_login
    }
    
    class ProductionBatch {
        +int batch_id
        +str product_type
        +float initial_weight
        +float final_weight
        +float target_concentration
        +datetime start_time
        +datetime end_time
        +str stage
    }
    
    class LabMeasurement {
        +int measurement_id
        +int batch_id
        +str parameter_name
        +float parameter_value
        +str parameter_unit
        +str lab_technician
        +datetime measurement_time
        +str notes
    }
    
    class IoTSensorData {
        +int sensor_id
        +int batch_id
        +str sensor_type
        +str sensor_location
        +float sensor_value
        +str sensor_unit
        +datetime time
    }
    
    class ActivityLog {
        +int log_id
        +str user_id
        +str action
        +str details
        +datetime timestamp
    }
    
    ProductionBatch "1" --> "*" LabMeasurement
    ProductionBatch "1" --> "*" IoTSensorData
    User "1" --> "*" ActivityLog
    User "1" --> "*" LabMeasurement : performs
```

### 4. State Diagram: Жизненный цикл производственной партии

```mermaid
stateDiagram-v2
    [*] --> Создана
    Создана --> Приемка: Начало производства
    Приемка --> Посол: Сырье принято
    Посол --> Термообработка: Посол завершен (72ч)
    Термообработка --> Сушка: T внутри ≥74°C
    Сушка --> Упаковка: Влажность достигнута
    Упаковка --> Хранение: Вакуумная упаковка
    Хранение --> Отгружена: Контроль качества пройден
    Отгружена --> [*]
    
    Приемка --> Отбракована: Не соответствует стандартам
    Посол --> Отбракована: pH вне нормы
    Термообработка --> Отбракована: Недостижение T°
    Отбракована --> [*]
```

### 5. Component Diagram: Структура приложения

```mermaid
graph TB
    subgraph "app.py - Main Application"
        MAIN[Main Controller]
        AUTH_CHECK[Authentication Check]
        NAVIGATION[Navigation Router]
    end
    
    subgraph "Authentication Module"
        AUTH[auth.py]
        LOGIN[Login Page]
        LOGOUT[Logout]
        PERMISSIONS[Permission Check]
    end
    
    subgraph "Pages"
        HOME[home.py]
        PRODUCTION[production.py]
        REGRESSION[regression.py]
        PH_MODEL[ph_modeling.py]
        EXPERIMENTS[experiments.py]
        DASHBOARD[dashboard.py]
        IOT_MON[iot_monitoring.py]
        REPORTS[reports.py]
        ADMIN[admin.py]
    end
    
    subgraph "Data Layer"
        DB_MODULE[database_supabase.py]
        DATA_LOADER[data_loader.py]
    end
    
    subgraph "IoT Infrastructure"
        MQTT_CLIENT[mqtt_client.py]
        IOT_FUNCTIONS[IoT Helper Functions]
    end
    
    subgraph "UI Components"
        UI_MODULE[ui.py]
        TRANSLATIONS[Language Support]
        CHARTS[Chart Generators]
    end
    
    MAIN --> AUTH_CHECK
    AUTH_CHECK --> AUTH
    AUTH_CHECK --> NAVIGATION
    
    NAVIGATION --> HOME
    NAVIGATION --> PRODUCTION
    NAVIGATION --> REGRESSION
    NAVIGATION --> PH_MODEL
    NAVIGATION --> EXPERIMENTS
    NAVIGATION --> DASHBOARD
    NAVIGATION --> IOT_MON
    NAVIGATION --> REPORTS
    NAVIGATION --> ADMIN
    
    HOME --> DB_MODULE
    PRODUCTION --> DB_MODULE
    REGRESSION --> DATA_LOADER
    PH_MODEL --> DB_MODULE
    DASHBOARD --> DB_MODULE
    IOT_MON --> DB_MODULE
    IOT_MON --> MQTT_CLIENT
    REPORTS --> DB_MODULE
    ADMIN --> DB_MODULE
    
    MQTT_CLIENT --> IOT_FUNCTIONS
    IOT_FUNCTIONS --> DB_MODULE
    
    ALL_PAGES[All Pages] --> UI_MODULE
    UI_MODULE --> TRANSLATIONS
    UI_MODULE --> CHARTS
```

### 6. Data Flow Diagram: Обработка лабораторных измерений

```mermaid
flowchart TD
    START([Начало]) --> INPUT[Ввод данных измерения]
    INPUT --> VALIDATE{Валидация данных}
    
    VALIDATE -->|Невалидно| ERROR1[Показать ошибку]
    ERROR1 --> INPUT
    
    VALIDATE -->|Валидно| CHECK_BATCH{Партия существует?}
    CHECK_BATCH -->|Нет| ERROR2[Ошибка: партия не найдена]
    ERROR2 --> INPUT
    
    CHECK_BATCH -->|Да| CHECK_PARAM{Параметр в списке?}
    CHECK_PARAM -->|Нет| ERROR3[Ошибка: неизвестный параметр]
    ERROR3 --> INPUT
    
    CHECK_PARAM -->|Да| SAVE[Сохранить в БД]
    SAVE --> LOG[Логировать действие]
    LOG --> CLEAR_CACHE[Очистить кэш]
    CLEAR_CACHE --> NOTIFY[Уведомление пользователя]
    NOTIFY --> UPDATE_UI[Обновить UI]
    UPDATE_UI --> END([Конец])
```

### 7. Deployment Diagram: Архитектура развертывания

```mermaid
graph TB
    subgraph "Client Layer"
        BROWSER[Web Browser]
        MOBILE[Mobile App Claude]
    end
    
    subgraph "Application Server"
        STREAMLIT[Streamlit App<br/>Port 8501]
        PYTHON[Python Runtime 3.9+]
    end
    
    subgraph "Database Layer"
        SUPABASE[Supabase Cloud<br/>PostgreSQL]
    end
    
    subgraph "IoT Infrastructure"
        MQTT_BROKER[Eclipse Mosquitto<br/>Port 1883]
        SENSORS_NET[IoT Sensors Network]
    end
    
    subgraph "External Services"
        SMTP[Email Server]
        STORAGE[Cloud Storage]
    end
    
    BROWSER --> STREAMLIT
    MOBILE --> STREAMLIT
    STREAMLIT --> PYTHON
    PYTHON --> SUPABASE
    PYTHON --> MQTT_BROKER
    MQTT_BROKER --> SENSORS_NET
    PYTHON --> SMTP
    PYTHON --> STORAGE
```

---

## 🚀 Установка и запуск

### Предварительные требования

```bash
Python 3.9+
PostgreSQL (через Supabase)
MQTT Broker (Eclipse Mosquitto)
```

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/zhaya-platform.git
cd zhaya-platform
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка Supabase

Создайте файл `.streamlit/secrets.toml`:

```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-anon-key"
db_url = "postgresql://postgres:password@db.supabase.co:5432/postgres"
```

### 5. Запуск MQTT брокера

**Вариант 1: Docker (рекомендуется)**
```bash
docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto
```

**Вариант 2: Локально**
```bash
# Linux/Mac
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Windows
# Скачать с https://mosquitto.org/download/
mosquitto -c mosquitto.conf
```

### 6. Запуск IoT симулятора (опционально)

```bash
python mqtt_client.py
```

### 7. Запуск приложения

```bash
streamlit run app.py
```

Откройте браузер: `http://localhost:8501`

### Тестовые учетные данные

```
Администратор:
Email: admin@zhaya.kz
Password: Admin123

Оператор:
Email: operator@zhaya.kz
Password: Operator123
```

---

## 📁 Структура проекта

```
zhaya-platform/
├── app.py                      # Главный файл приложения
├── auth.py                     # Модуль аутентификации
├── ui.py                       # UI компоненты и локализация
├── database_supabase.py        # Работа с Supabase
├── data_loader.py              # Загрузка локальных данных
├── mqtt_client.py              # IoT симулятор и MQTT клиент
├── requirements.txt            # Зависимости Python
├── README.md                   # Документация (этот файл)
├── IOT.md                      # Руководство по IoT
│
├── .streamlit/
│   └── secrets.toml            # Конфигурация (не коммитится)
│
├── pages/                      # Страницы приложения
│   ├── home.py                 # Главная страница
│   ├── dashboard.py            # Dashboard с KPI
│   ├── production.py           # Процесс производства
│   ├── regression.py           # Регрессионный анализ
│   ├── ph_modeling.py          # pH моделирование
│   ├── mathematical_models.py  # Математические модели
│   ├── seabuckthorn.py         # Анализ облепихи
│   ├── experiments.py          # Эксперименты
│   ├── digital_safety.py       # Цифровые технологии
│   ├── data_exploration.py     # Исследование данных
│   ├── history_db.py           # История измерений
│   ├── iot_monitoring.py       # IoT мониторинг
│   ├── reports.py              # Отчеты
│   ├── admin.py                # Админ-панель
│   └── supabase_test.py        # Тестирование Supabase
│
├── data/                       # Локальные данные (CSV/Excel)
│   ├── meat_data.xlsx
│   ├── opyty.xlsx
│   └── *.csv
│
└── docs/                       # Дополнительная документация
    ├── API.md
    ├── DATABASE_SCHEMA.md
    └── IoT_SETUP.md
```

---

## 🔧 Модули и функциональность

### 1. Аутентификация (`auth.py`)

**Функции:**
- `authenticate_user(email, password)` — аутентификация с хешированием
- `check_permission(user_role, permission)` — проверка прав доступа
- `logout_user()` — выход из системы
- `log_activity(user_id, action, details)` — логирование действий

**Роли и права:**

| Роль          | Права                                                      |
|---------------|------------------------------------------------------------|
| **admin**     | Все права (управление пользователями, настройки системы)   |
| **manager**   | Просмотр отчетов, управление производством, история       |
| **analyst**   | Просмотр аналитики, отчетов, истории                      |
| **operator**  | Ввод данных, базовый просмотр dashboard                   |

### 2. База данных (`database_supabase.py`)

**Основные таблицы:**

```sql
-- Пользователи
users (user_id, email, password_hash, full_name, role, department, is_active, created_at, last_login)

-- Производственные партии
production_batches (batch_id, product_type, initial_weight, final_weight, target_sea_buckthorn_concentration, start_time, end_time, stage)

-- Лабораторные измерения
lab_measurements (measurement_id, batch_id, parameter_name, parameter_value, parameter_unit, lab_technician, measurement_time, notes)

-- IoT данные
iot_sensor_data (sensor_id, batch_id, sensor_type, sensor_location, sensor_value, sensor_unit, time)

-- Команды актуаторам
actuator_logs (log_id, batch_id, actuator_name, set_value, previous_value, change_time, changed_by)

-- Логи активности
activity_logs (log_id, user_id, action, details, timestamp)
```

**Ключевые функции:**
- `fetch_production_batches()` — получение партий
- `create_production_batch()` — создание новой партии
- `add_lab_measurement()` — добавление измерения
- `fetch_iot_sensor_data()` — получение данных IoT
- `get_batch_details()` — детальная информация о партии

### 3. IoT система (`mqtt_client.py`)

**Типы датчиков:**
- `temperature` — температура (°C)
- `humidity` — влажность (%)
- `water_activity` — активность воды (Aw)
- `ph` — кислотность
- `orp` — окислительно-восстановительный потенциал (mV)
- `weight` — масса (г)
- `pressure` — давление (МПа)
- `air_flow` — скорость воздушного потока (м/с)

**Локации датчиков:**
- `product_mass` — в массе продукта
- `chamber_air` — в воздухе камеры
- `press` — в прессе
- `brine_tank` — в баке с рассолом

**Топики MQTT:**
```
zhaya/sensors/data       # Данные датчиков (публикация симулятором)
zhaya/actuators/commands # Команды управления (подписка симулятором)
zhaya/system/status      # Статус системы
```

### 4. Локализация (`ui.py`)

**Поддерживаемые языки:**
- 🇷🇺 Русский (`ru`)
- 🇬🇧 English (`en`)
- 🇰🇿 Қазақша (`kk`)

**Использование:**
```python
from ui import get_text

# Получение перевода
title = get_text("menu_home", lang_choice)  # "Главная" / "Home" / "Басты бет"
```

---

## 📡 API и интеграции

### REST API (через Supabase)

Все операции с БД выполняются через Supabase REST API:

```python
from database_supabase import init_supabase

supabase = init_supabase()

# SELECT
response = supabase.table('production_batches').select('*').execute()

# INSERT
response = supabase.table('lab_measurements').insert(data).execute()

# UPDATE
response = supabase.table('users').update({'is_active': False}).eq('user_id', user_id).execute()

# DELETE
response = supabase.table('activity_logs').delete().eq('log_id', log_id).execute()
```

### MQTT API

**Публикация данных датчиков:**
```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("localhost", 1883)

sensor_data = {
    "batch_id": 1,
    "sensor_type": "temperature",
    "sensor_location": "product_mass",
    "sensor_value": 45.2,
    "sensor_unit": "°C",
    "time": "2025-12-09T10:30:00Z"
}

client.publish("zhaya/sensors/data", json.dumps(sensor_data))
```

**Отправка команды актуатору:**
```python
command = {
    "batch_id": 1,
    "actuator_name": "T_set",
    "set_value": 47.0,
    "changed_by": "operator@zhaya.kz"
}

client.publish("zhaya/actuators/commands", json.dumps(command))
```

---

## 🔒 Безопасность

### 1. Аутентификация

- **Хеширование паролей:** SHA-256
- **Сессии:** Токены длиной 32 байта (URL-safe)
- **Время жизни сессии:** 8 часов
- **Логирование:** Все попытки входа записываются в `activity_logs`

### 2. Авторизация

```python
# Проверка прав доступа
if check_permission(user_role, "view_reports"):
    show_reports()
else:
    st.error("❌ Доступ запрещен")
```

### 3. Валидация данных

```python
# Валидация email
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Валидация пароля
def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Минимум 8 символов"
    if not any(c.isupper() for c in password):
        return False, "Хотя бы одна заглавная буква"
    if not any(c.isdigit() for c in password):
        return False, "Хотя бы одна цифра"
    return True, "OK"
```

### 4. Защита от SQL-инъекций

Используется Supabase ORM с параметризованными запросами:
```python
# Безопасно
response = supabase.table('users').select('*').eq('email', user_email).execute()

# Опасно (НЕ используется)
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # ❌
```

---

## 📊 Мониторинг и IoT

### Архитектура IoT

```
IoT Датчики → MQTT Broker → mqtt_client.py → Supabase → Dashboard
```

### Реальное время (Real-time)

**Автообновление дашборда:**
```python
auto_refresh = st.checkbox("🔄 Автообновление", value=True)

if auto_refresh:
    refresh_interval = st.slider("Интервал (сек)", 1, 30, 5)
    time.sleep(refresh_interval)
    st.rerun()
```

### Алерты и уведомления

```python
# Проверка pH диапазона
if 5.1 <= ph_value <= 5.6:
    st.success("✅ pH в норме")
else:
    st.warning(f"⚠️ pH вне нормы: {ph_value:.2f}")
    # Отправка уведомления
    send_alert(user_email, f"pH партии {batch_id} = {ph_value}")
```

### Управление актуаторами

```python
# Отправка команды через UI
if st.button("Применить температуру"):
    success = send_actuator_command(
        batch_id=1,
        actuator_name="T_set",
        set_value=45.0,
        changed_by=user_email
    )
    if success:
        st.success("✅ Команда отправлена")
```

---

## 👨‍💻 Руководство разработчика

### Добавление новой страницы

**1. Создайте файл `pages/my_page.py`:**
```python
import streamlit as st

def show_my_page(lang_choice):
    st.title("Моя страница")
    st.write("Содержимое...")
```

**2. Добавьте импорт в `app.py`:**
```python
from pages.my_page import show_my_page
```

**3. Добавьте в навигацию:**
```python
# В секции navigation
page_options.append(("📄 Моя страница", "my_page"))

# В секции роутинга
elif page == "my_page":
    show_my_page(lang_choice)
```

### Добавление переводов

**В `ui.py` (словарь `LANG`):**
```python
LANG = {
    "ru": {
        "my_key": "Моя строка",
    },
    "en": {
        "my_key": "My string",
    },
    "kk": {
        "my_key": "Менің жолым",
    }
}
```

**Использование:**
```python
from ui import get_text

text = get_text("my_key", lang_choice)
```

### Работа с кэшем

```python
import streamlit as st

# Кэширование данных (на 5 минут)
@st.cache_data(ttl=300)
def fetch_heavy_data():
    # Тяжелый запрос
    return data

# Очистка кэша
from database_supabase import clear_all_caches
clear_all_caches()
```

### Логирование действий

```python
from auth import log_activity

# Логирование
log_activity(
    user_id=user["id"],
    action="create_batch",
    details=f"Создана партия ID: {batch_id}"
)
```

### Тестирование

```python
# Запуск тестов (pytest)
pytest tests/

# Тестирование Supabase подключения
streamlit run app.py
# Перейдите в "🔧 Тест Supabase"
```

---

## 📞 Поддержка и контакты

**Техническая поддержка:**
- Email: support@zhaya.kz
- Telegram: @zhaya_support

**Документация:**
- [API Reference](docs/API.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [IoT Setup Guide](IOT.md)

**Разработчики:**
- Lead Developer: [Ваше имя]
- Project Manager: [Менеджер проекта]

---

## 📄 Лицензия

```
MIT License

Copyright (c) 2025 Zhaya Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software")...
```

---

## 🎉 Благодарности

- **Streamlit** — за отличный фреймворк UI
- **Supabase** — за мощную backend-платформу
- **Eclipse Mosquitto** — за надежный MQTT брокер
- **Plotly** — за интерактивные графики

---

**Версия документации:** 2.0  
**Последнее обновление:** 09.12.2025
