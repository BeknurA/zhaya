# mqtt_client.py - IoT симулятор для производства Жая
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime
from supabase import create_client, Client
import streamlit as st

# =================================================================
# === КОНФИГУРАЦИЯ ===
# =================================================================

# MQTT брокер
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# Топики MQTT
TOPIC_SENSORS = "zhaya/sensors/data"
TOPIC_ACTUATORS = "zhaya/actuators/commands"
TOPIC_STATUS = "zhaya/system/status"

# Supabase (из secrets)
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    # Для автономного запуска (без Streamlit)
    SUPABASE_URL = "https://lfvimyjlbckcvnuponvt.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxmdmlteWpsYmNrY3ZudXBvbnZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NTExMzYsImV4cCI6MjA3ODQyNzEzNn0.stnX342ED3dt2lL5wtIcZ5ZnoXI2SYvLBzt851723J0"
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =================================================================
# === ПАРАМЕТРЫ СИМУЛЯЦИИ ===
# =================================================================

# Параметры производственного процесса (на основе документации)
PROCESS_STAGES = {
    "разделка": {"duration": 3600, "temp_range": (2, 4)},
    "посол": {"duration": 259200, "temp_range": (0, 3)},  # 72 часа
    "прессование": {"duration": 7200, "temp_range": (16, 18)},
    "формование": {"duration": 1800, "temp_range": (18, 20)},
    "сушка": {"duration": 14400, "temp_range": (43, 47)},  # 4 часа
    "созревание": {"duration": 86400, "temp_range": (10, 14)},  # 24 часа
    "хранение": {"duration": 172800, "temp_range": (0, 5)}  # 48+ часов
}

# Типы датчиков из схемы БД
SENSOR_TYPES = [
    'temperature',
    'humidity', 
    'weight',
    'water_activity',
    'ph',
    'orp',
    'pressure',
    'air_flow'
]

# Локации датчиков
SENSOR_LOCATIONS = [
    'product_mass',
    'chamber_air',
    'press',
    'brine_tank'
]

# =================================================================
# === MQTT CLIENT ===
# =================================================================

class IoTSimulator:
    def __init__(self, batch_id: int = 1):
        self.batch_id = batch_id
        self.client = mqtt.Client(client_id=f"zhaya_simulator_{batch_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.connected = False
        self.running = False
        
        # Состояние процесса
        self.current_stage = "посол"
        self.stage_start_time = time.time()
        self.cycle_count = 0
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback при подключении к брокеру"""
        if rc == 0:
            print(f"✅ Подключено к MQTT брокеру: {MQTT_BROKER}:{MQTT_PORT}")
            self.connected = True
            
            # Подписка на топик команд актуаторов
            client.subscribe(TOPIC_ACTUATORS)
            print(f"📡 Подписка на топик: {TOPIC_ACTUATORS}")
            
            # Отправка статуса системы
            self.publish_status("online")
        else:
            print(f"❌ Ошибка подключения. Код: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback при отключении"""
        print(f"⚠️ Отключено от брокера. Код: {rc}")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback при получении сообщения"""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"📩 Получена команда: {payload}")
            
            # Обработка команд актуаторов
            if msg.topic == TOPIC_ACTUATORS:
                self.handle_actuator_command(payload)
                
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
    
    def connect(self):
        """Подключение к MQTT брокеру"""
        try:
            print(f"🔌 Подключение к MQTT брокеру {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.client.loop_start()
            
            # Ожидание подключения
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.5)
            
            if not self.connected:
                print("❌ Таймаут подключения")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключение от брокера"""
        self.running = False
        self.publish_status("offline")
        self.client.loop_stop()
        self.client.disconnect()
        print("👋 Отключено от MQTT брокера")
    
    def publish_status(self, status: str):
        """Публикация статуса системы"""
        message = {
            "batch_id": self.batch_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "stage": self.current_stage
        }
        self.client.publish(TOPIC_STATUS, json.dumps(message))
    
    def generate_sensor_data(self, sensor_type: str, location: str) -> dict:
        """Генерация реалистичных данных датчиков на основе стадии процесса"""
        
        stage_params = PROCESS_STAGES.get(self.current_stage, PROCESS_STAGES["посол"])
        temp_min, temp_max = stage_params["temp_range"]
        
        # Базовые значения в зависимости от типа датчика
        if sensor_type == "temperature":
            if location == "product_mass":
                # Температура продукта (немного отличается от камеры)
                value = random.uniform(temp_min, temp_max) + random.uniform(-0.5, 0.5)
            else:
                value = random.uniform(temp_min, temp_max)
            unit = "°C"
            
        elif sensor_type == "humidity":
            # Влажность (зависит от стадии)
            if self.current_stage == "сушка":
                value = random.uniform(40, 55)
            elif self.current_stage == "посол":
                value = random.uniform(75, 85)
            else:
                value = random.uniform(60, 70)
            unit = "%"
            
        elif sensor_type == "weight":
            # Масса продукта (уменьшается при сушке)
            base_weight = 1000  # 1 кг исходная масса
            if self.current_stage == "сушка":
                loss_factor = random.uniform(0.12, 0.18)  # 12-18% потери
                value = base_weight * (1 - loss_factor)
            else:
                value = base_weight + random.uniform(-10, 10)
            unit = "g"
            
        elif sensor_type == "water_activity":
            # Активность воды (целевой диапазон 0.88-0.90)
            if self.current_stage in ["сушка", "созревание"]:
                value = random.uniform(0.86, 0.92)
            else:
                value = random.uniform(0.93, 0.97)
            unit = "aw"
            
        elif sensor_type == "ph":
            # pH (целевой диапазон 5.1-5.6)
            if self.current_stage == "посол":
                # pH снижается во время посола (от 6.5 до 5.3)
                elapsed_hours = (time.time() - self.stage_start_time) / 3600
                total_hours = stage_params["duration"] / 3600
                progress = min(elapsed_hours / total_hours, 1.0)
                value = 6.5 - (1.2 * progress) + random.uniform(-0.1, 0.1)
            else:
                value = random.uniform(5.1, 5.6)
            unit = "pH"
            
        elif sensor_type == "orp":
            # Окислительно-восстановительный потенциал
            value = random.uniform(150, 300)
            unit = "mV"
            
        elif sensor_type == "pressure":
            # Давление (для прессования)
            if self.current_stage == "прессование":
                value = random.uniform(1.2, 1.5)  # МПа
            else:
                value = 0.1
            unit = "MPa"
            
        elif sensor_type == "air_flow":
            # Скорость воздушного потока (для сушки)
            if self.current_stage in ["сушка", "созревание"]:
                value = random.uniform(0.3, 0.8)
            else:
                value = 0.1
            unit = "m/s"
        else:
            value = random.uniform(0, 100)
            unit = "units"
        
        return {
            "batch_id": self.batch_id,
            "sensor_type": sensor_type,
            "sensor_location": location,
            "sensor_value": round(value, 3),
            "sensor_unit": unit,
            "time": datetime.utcnow().isoformat(),
            "stage": self.current_stage
        }
    
    def save_to_database(self, sensor_data: dict):
        """Сохранение данных в Supabase"""
        try:
            # Подготовка данных для вставки
            db_data = {
                "batch_id": sensor_data["batch_id"],
                "sensor_type": sensor_data["sensor_type"],
                "sensor_location": sensor_data["sensor_location"],
                "sensor_value": sensor_data["sensor_value"],
                "sensor_unit": sensor_data["sensor_unit"],
                "time": sensor_data["time"]
            }
            
            # Вставка в таблицу iot_sensor_data
            result = supabase.table("iot_sensor_data").insert(db_data).execute()
            
            if result.data:
                print(f"💾 Сохранено в БД: {sensor_data['sensor_type']} = {sensor_data['sensor_value']} {sensor_data['sensor_unit']}")
                return True
            else:
                print(f"⚠️ Не удалось сохранить в БД")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка сохранения в БД: {e}")
            return False
    
    def publish_sensor_data(self):
        """Публикация данных всех датчиков"""
        sensor_readings = []
        
        # Генерация показаний для каждой комбинации датчик-локация
        for sensor_type in SENSOR_TYPES:
            for location in SENSOR_LOCATIONS:
                # Не все датчики используются во всех локациях
                if self.is_sensor_valid_for_location(sensor_type, location):
                    sensor_data = self.generate_sensor_data(sensor_type, location)
                    sensor_readings.append(sensor_data)
                    
                    # Публикация в MQTT
                    self.client.publish(TOPIC_SENSORS, json.dumps(sensor_data))
                    
                    # Сохранение в БД
                    self.save_to_database(sensor_data)
        
        return sensor_readings
    
    def is_sensor_valid_for_location(self, sensor_type: str, location: str) -> bool:
        """Проверка валидности комбинации датчик-локация"""
        # Логика размещения датчиков
        valid_combinations = {
            'temperature': ['product_mass', 'chamber_air', 'brine_tank'],
            'humidity': ['chamber_air'],
            'weight': ['product_mass'],
            'water_activity': ['product_mass'],
            'ph': ['product_mass', 'brine_tank'],
            'orp': ['product_mass', 'brine_tank'],
            'pressure': ['press'],
            'air_flow': ['chamber_air']
        }
        
        return location in valid_combinations.get(sensor_type, [])
    
    def handle_actuator_command(self, command: dict):
        """Обработка команд управления актуаторами"""
        try:
            actuator_name = command.get("actuator_name")
            set_value = command.get("set_value")
            
            print(f"🎛️ Команда актуатору: {actuator_name} = {set_value}")
            
            # Логирование команды в БД (таблица actuator_logs)
            log_data = {
                "batch_id": self.batch_id,
                "actuator_name": actuator_name,
                "set_value": set_value,
                "previous_value": command.get("previous_value", 0),
                "change_time": datetime.utcnow().isoformat(),
                "changed_by": command.get("changed_by", "mqtt_client")
            }
            
            supabase.table("actuator_logs").insert(log_data).execute()
            print(f"✅ Команда актуатору сохранена в БД")
            
        except Exception as e:
            print(f"❌ Ошибка обработки команды: {e}")
    
    def simulate_stage_transition(self):
        """Симуляция перехода между стадиями процесса"""
        elapsed_time = time.time() - self.stage_start_time
        stage_params = PROCESS_STAGES.get(self.current_stage, PROCESS_STAGES["посол"])
        
        # Переход на следующую стадию (ускоренная симуляция - 1 минута = 1 час)
        if elapsed_time > (stage_params["duration"] / 60):  # Ускорение x60
            stages_list = list(PROCESS_STAGES.keys())
            current_index = stages_list.index(self.current_stage)
            
            if current_index < len(stages_list) - 1:
                self.current_stage = stages_list[current_index + 1]
                self.stage_start_time = time.time()
                print(f"🔄 Переход на стадию: {self.current_stage}")
                self.publish_status("stage_changed")
    
    def run(self, interval: int = 5, duration: int = None):
        """
        Запуск симуляции
        :param interval: Интервал публикации данных (секунды)
        :param duration: Длительность симуляции (секунды), None = бесконечно
        """
        if not self.connected:
            print("❌ Не подключено к брокеру")
            return
        
        self.running = True
        start_time = time.time()
        
        print(f"🚀 Запуск симуляции для партии ID: {self.batch_id}")
        print(f"⏱️ Интервал публикации: {interval} сек")
        print(f"📊 Начальная стадия: {self.current_stage}")
        print("-" * 60)
        
        try:
            while self.running:
                # Публикация данных датчиков
                print(f"\n🔹 Цикл #{self.cycle_count + 1} | Стадия: {self.current_stage}")
                sensor_readings = self.publish_sensor_data()
                
                # Симуляция переходов между стадиями
                self.simulate_stage_transition()
                
                self.cycle_count += 1
                
                # Проверка длительности симуляции
                if duration and (time.time() - start_time) >= duration:
                    print(f"\n✅ Симуляция завершена (длительность: {duration} сек)")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⚠️ Симуляция прервана пользователем")
        finally:
            self.disconnect()

# =================================================================
# === ФУНКЦИИ ДЛЯ ИСПОЛЬЗОВАНИЯ В STREAMLIT ===
# =================================================================

def get_latest_sensor_data(batch_id: int = None, limit: int = 100):
    """Получение последних данных датчиков из БД"""
    try:
        query = supabase.table("iot_sensor_data") \
            .select("*") \
            .order("time", desc=True) \
            .limit(limit)
        
        if batch_id:
            query = query.eq("batch_id", batch_id)
        
        result = query.execute()
        return result.data
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return []

def send_actuator_command(batch_id: int, actuator_name: str, set_value: float, 
                          changed_by: str = "streamlit"):
    """Отправка команды актуатору через MQTT"""
    try:
        client = mqtt.Client(client_id="streamlit_command_sender")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        command = {
            "batch_id": batch_id,
            "actuator_name": actuator_name,
            "set_value": set_value,
            "changed_by": changed_by,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.publish(TOPIC_ACTUATORS, json.dumps(command))
        client.disconnect()
        
        print(f"✅ Команда отправлена: {actuator_name} = {set_value}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки команды: {e}")
        return False

# =================================================================
# === MAIN (для автономного запуска) ===
# =================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🐎 MQTT IoT Симулятор для производства Жая")
    print("=" * 60)
    
    # Создание симулятора для партии ID=1
    simulator = IoTSimulator(batch_id=1)
    
    # Подключение к брокеру
    if simulator.connect():
        # Запуск симуляции (интервал 5 сек, бесконечно)
        simulator.run(interval=5, duration=None)
    else:
        print("❌ Не удалось запустить симуляцию")