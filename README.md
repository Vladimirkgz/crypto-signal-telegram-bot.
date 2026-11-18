# Crypto Signal Telegram Bot

Независимый Telegram-бот для уведомлений о сигналах сканера.

- Проверяет JSON-ленту раз в 5 минут через GitHub Actions.
- Отправляет новые сигналы WAITING_TRIGGER и TRIGGERED.
- Не отправляет повторно уже обработанные ID.
- Игнорирует сигналы старше 24 часов.
- Не совершает торговых операций.

## GitHub Secrets

В Settings → Secrets and variables → Actions добавьте:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Запуск вручную: Actions → Telegram signal notifications → Run workflow.
