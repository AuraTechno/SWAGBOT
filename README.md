# Деплой SWAG VPN Bot на сервер

## 1. Подготовка сервера

```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Клонирование репозитория
git clone https://github.com/AuraTechno/SWAGBOT.git
cd SWAGBOT

# Создать .env из шаблона
nano .env
```

## 2. Настройка .env на сервере

Впиши в `.env`:
```
BOT_TOKEN=...              # Токен бота
REQUIRED_CHANNEL_ID=...    # ID канала
REQUIRED_CHANNEL_URL=...   # Ссылка на канал
ADMIN_IDS=...              # Твой Telegram ID

REMNAWAVE_BASE_URL=https://твой-домен-панели
REMNAWAVE_TOKEN=...        # Из панели Remnawave
REMNAWAVE_NODE_UUID=...    # Из панели Remnawave
```

## 3. Запуск

```bash
# Запустить бота
sudo docker compose up -d

# Проверить логи
sudo docker compose logs --tail=50 -f
```

## 4. Быстрое обновление (после git push)

```bash
cd ~/SWAGBOT && ./update.sh
```

## Полезные команды

```bash
# Статус
sudo docker compose ps

# Логи
sudo docker compose logs --tail=50

# Остановить
sudo docker compose down

# Перезапустить
sudo docker compose restart

# Сбросить БД (удалит все данные!)
sudo docker compose down
sudo rm -f data/bot.db
sudo docker compose up -d
```
