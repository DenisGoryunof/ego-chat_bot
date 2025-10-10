import sys
import os

# Добавляем путь к вашему приложению
path = '/home/xDenGor/ego-chat_bot'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application