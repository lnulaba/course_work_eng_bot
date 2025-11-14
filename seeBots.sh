#!/bin/bash

# Назва процесу, який ви хочете відслідковувати
process_name="python3"

# Отримуємо список PID процесів з вказаною назвою
pids=$(pgrep -f python3 | tr '\n' ',' |sed 's/,$//')
#echo "$pids"
# Перевірка, чи є процеси з цією назвою
if [ -n "$pids" ]; then
    # Запускаємо команду top з вказаними PID процесів
    top -p "$pids" -c
else
    echo "Процеси з ім'ям $process_name не знайдено."
fi
