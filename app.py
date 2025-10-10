from flask import Flask, request
import os
import logging
import threading
import subprocess
import sys
from datetime import datetime

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Флаг для отслеживания состояния бота
bot_process = None
bot_running = False

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Beauty Salon Bot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status { padding: 20px; border-radius: 10px; margin: 20px 0; }
                .active { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .inactive { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .button { display: inline-block; padding: 10px 20px; margin: 5px; 
                         background-color: #007bff; color: white; text-decoration: none; 
                         border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>💅 Beauty Salon Bot</h1>
            <div class="status active">
                <h2>✅ Статус: Активен</h2>
                <p>Бот для записи в салон красоты работает</p>
                <p>Время сервера: {}</p>
            </div>
            <div>
                <a href="/health-check" class="button">Проверка здоровья</a>
                <a href="/status" class="button">Статус</a>
                <a href="/restart" class="button">Перезапуск</a>
            </div>
        </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/health-check')
def health_check():
    """Endpoint для проверки здоровья"""
    try:
        # Проверяем, что основные файлы существуют
        required_files = ['bot.py', 'app.py', '.env']
        for file in required_files:
            if not os.path.exists(file):
                return f"File {file} missing", 500
        
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/status')
def status():
    """Подробный статус системы"""
    status_info = {
        "status": "active",
        "service": "Beauty Salon Bot",
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "files": {
            "bot.py": os.path.exists('bot.py'),
            "app.py": os.path.exists('app.py'),
            ".env": os.path.exists('.env'),
            "bookings.json": os.path.exists('bookings.json'),
            "bookings.db": os.path.exists('bookings.db')
        }
    }
    return status_info

@app.route('/restart')
def restart():
    """Перезапуск бота"""
    try:
        # Здесь можно добавить логику перезапуска бота
        # Например, запуск бота в отдельном процессе
        return "Бот готов к работе. Используйте scheduled tasks для автоматического перезапуска.", 200
    except Exception as e:
        return f"Ошибка: {e}", 500

@app.route('/start-bot')
def start_bot():
    """Запуск бота через веб-интерфейс"""
    global bot_process, bot_running
    
    try:
        if bot_running:
            return "Бот уже запущен", 200
            
        # Запускаем бота в отдельном процессе
        bot_process = subprocess.Popen([sys.executable, 'bot.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        bot_running = True
        
        return "Бот запущен", 200
    except Exception as e:
        return f"Ошибка запуска бота: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)