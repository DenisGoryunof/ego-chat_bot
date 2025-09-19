
#!/bin/bash

echo "🚀 Установка и запуск бота для записи на процедуры"

# Проверяем установлен ли Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Установите Python3 сначала."
    exit 1
fi

# Создаем виртуальное окружение
echo "📦 Создаем виртуальное окружение..."
python3 -m venv venv

# Активируем виртуальное окружение
echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Устанавливаем зависимости..."
pip install -r requirements.txt

# Копируем пример .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создаем файл .env из примера..."
    cp .env.example .env
    echo "⚠️ Отредактируйте файл .env и добавьте ваш BOT_TOKEN"
fi

# Создаем файл для записей если его нет
if [ ! -f bookings.json ]; then
    echo "📋 Создаем файл для записей..."
    echo "[]" > bookings.json
fi

echo "✅ Установка завершена!"
echo "🎯 Для запуска бота выполните:"
echo "   source venv/bin/activate && python bot.py"
echo ""
echo "📋 Для работы на PythonAnywhere:"
echo "   1. Загрузите все файлы на сервер"
echo "   2. Создайте .env файл с вашими настройками"
echo "   3. Установите зависимости: pip install -r requirements.txt"
echo "   4. Запустите бота: python bot.py"
