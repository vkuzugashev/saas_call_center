# Service Management API (app_pm)

## 📌 Описание
Flask-приложение для управления сервисами через HTTP-запросы. Выполняет сборку, запуск, остановку и мониторинг сервисов с использованием внешнего скрипта `service_control.py`.

---

## 🛠️ Требования
- Python 3.8+
- Flask
- python-dotenv
- ОС: Windows или Linux

Установите зависимости:
```
pip install -r requirements.txt
```

## Конфигурация
Создайте .env в папке:

```
# Путь к директории со скриптами (по умолчанию: ../../scripts)
SCRIPT_PATH=../../scripts

# Имя основного скрипта управления сервисами (по умолчанию: service_control.py)
SERVICE_CONTROL_SCRIPT=service_control.py

# Интервал проверки сервисов в секундах (по умолчанию: 60)
SERVICE_MONITOR_INTERVAL=60

# Уровень логирования (DEBUG/INFO/ERROR)
LOG_LEVEL=DEBUG
```

## Запуск
```
python3 app_pm.py
```

## API Endpoints

### Сборка сервиса

POST /service/build/<service_name>
Пример:
```
curl -X POST http://localhost:8888/service/build/my_service
```

### Запуск сервиса

POST /service/start/<service_name>


### Получение статуса

GET /service/status/<service_name>
Ответ:
```
{
  "my_service": "running",
  "another_service": "stopped"
}
```

### Мониторинг
При запуске автоматически создается отдельный поток, который каждые SERVICE_MONITOR_INTERVAL секунд:
- Проверяет статус всех сервисов
- Автоматически запускает те, которые завершили работу
- Поддерживает сигналы SIGINT/SIGTERM для корректного завершения