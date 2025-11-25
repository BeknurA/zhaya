-- migration.sql
-- Этот скрипт необходимо выполнить в базе данных PostgreSQL для настройки таблиц,
-- необходимых для динамических дашбордов и отчетов.

-- Таблица для дашбордов
CREATE TABLE IF NOT EXISTS public.dashboards (
    dashboard_id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_kk VARCHAR(255),
    description_ru TEXT,
    description_en TEXT,
    description_kk TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    allowed_roles JSONB DEFAULT '["admin"]'::jsonb
);

-- Таблица для отдельных отчетов (графики, KPI, таблицы)
CREATE TABLE IF NOT EXISTS public.reports (
    report_id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('kpi', 'line_chart', 'bar_chart', 'table', 'pie_chart')),
    name_ru VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    name_kk VARCHAR(255),
    description_ru TEXT,
    description_en TEXT,
    description_kk TEXT,
    query TEXT NOT NULL,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для связи дашбордов и отчетов
CREATE TABLE IF NOT EXISTS public.dashboard_reports (
    dashboard_id INTEGER NOT NULL REFERENCES public.dashboards(dashboard_id) ON DELETE CASCADE,
    report_id INTEGER NOT NULL REFERENCES public.reports(report_id) ON DELETE CASCADE,
    position_row INTEGER NOT NULL DEFAULT 0,
    position_col INTEGER NOT NULL DEFAULT 0,
    width INTEGER NOT NULL DEFAULT 1,
    height INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (dashboard_id, report_id)
);

-- Вставка начальных данных для демонстрации
-- (можно закомментировать, если не нужно)

-- 1. Создание "Основного дашборда"
-- Сначала проверяем, существует ли уже дашборд с таким именем
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.dashboards WHERE name_ru = 'Основной дашборд') THEN
        INSERT INTO public.dashboards (name_ru, name_en, description_ru, allowed_roles)
        VALUES
        ('Основной дашборд', 'Main Dashboard', 'Ключевые показатели производственного процесса.', '["admin", "manager", "analyst"]');
    END IF;
END $$;

-- 2. Создание примеров отчетов
-- (с проверкой на существование)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.reports WHERE name_ru = 'Всего партий') THEN
        INSERT INTO public.reports (type, name_ru, name_en, query, config)
        VALUES
        ('kpi', 'Всего партий', 'Total Batches', 'SELECT COUNT(*) FROM public.production_batches;', '{"prefix": "📦", "suffix": " партий"}');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM public.reports WHERE name_ru = 'Средний вес сырья') THEN
        INSERT INTO public.reports (type, name_ru, name_en, query, config)
        VALUES
        ('kpi', 'Средний вес сырья', 'Avg. Initial Weight', 'SELECT AVG(initial_weight) FROM public.production_batches;', '{"prefix": "⚖️", "suffix": " кг", "decimals": 2}');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM public.reports WHERE name_ru = 'Партии по типам продуктов') THEN
        INSERT INTO public.reports (type, name_ru, name_en, query, config)
        VALUES
        ('bar_chart', 'Партии по типам продуктов', 'Batches by Product Type', 'SELECT product_type, COUNT(*) as count FROM public.production_batches GROUP BY product_type;', '{"x_axis": "product_type", "y_axis": "count", "title": "Распределение по типам"}');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM public.reports WHERE name_ru = 'Динамика pH (партия 1)') THEN
        INSERT INTO public.reports (type, name_ru, name_en, query, config)
        VALUES
        ('line_chart', 'Динамика pH (партия 1)', 'pH Dynamics (Batch 1)', 'SELECT time, sensor_value FROM public.iot_sensor_data WHERE batch_id = 1 AND sensor_type = ''ph'' ORDER BY time;', '{"x_axis": "time", "y_axis": "sensor_value", "title": "Изменение pH со временем"}');
    END IF;
END $$;

-- 3. Связывание отчетов с дашбордом
-- (с проверкой на существование)
DO $$
DECLARE
    dashboard_id_val INT;
    report_id_1 INT;
    report_id_2 INT;
    report_id_3 INT;
    report_id_4 INT;
BEGIN
    SELECT dashboard_id INTO dashboard_id_val FROM public.dashboards WHERE name_ru = 'Основной дашборд';
    SELECT report_id INTO report_id_1 FROM public.reports WHERE name_ru = 'Всего партий';
    SELECT report_id INTO report_id_2 FROM public.reports WHERE name_ru = 'Средний вес сырья';
    SELECT report_id INTO report_id_3 FROM public.reports WHERE name_ru = 'Партии по типам продуктов';
    SELECT report_id INTO report_id_4 FROM public.reports WHERE name_ru = 'Динамика pH (партия 1)';

    IF dashboard_id_val IS NOT NULL THEN
        IF report_id_1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.dashboard_reports WHERE dashboard_id = dashboard_id_val AND report_id = report_id_1) THEN
            INSERT INTO public.dashboard_reports (dashboard_id, report_id, position_row, position_col, width, height) VALUES (dashboard_id_val, report_id_1, 0, 0, 1, 1);
        END IF;
        IF report_id_2 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.dashboard_reports WHERE dashboard_id = dashboard_id_val AND report_id = report_id_2) THEN
            INSERT INTO public.dashboard_reports (dashboard_id, report_id, position_row, position_col, width, height) VALUES (dashboard_id_val, report_id_2, 0, 1, 1, 1);
        END IF;
        IF report_id_3 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.dashboard_reports WHERE dashboard_id = dashboard_id_val AND report_id = report_id_3) THEN
            INSERT INTO public.dashboard_reports (dashboard_id, report_id, position_row, position_col, width, height) VALUES (dashboard_id_val, report_id_3, 1, 0, 2, 2);
        END IF;
        IF report_id_4 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM public.dashboard_reports WHERE dashboard_id = dashboard_id_val AND report_id = report_id_4) THEN
            INSERT INTO public.dashboard_reports (dashboard_id, report_id, position_row, position_col, width, height) VALUES (dashboard_id_val, report_id_4, 1, 2, 2, 2);
        END IF;
    END IF;
END $$;
