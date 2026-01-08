import telebot
import requests
import json

TOKEN = "8589425051:AAE2wm9DQdq5a7WL6sKzaHtbeSpZVeXfutg"
bot = telebot.TeleBot(TOKEN)

# Хранение состояния пользователей
user_states = {}

# Ресурсы по категориям
RESOURCES = {
    "Тестирование": [
        ("Software Testing Help", "https://www.softwaretestinghelp.com", "Статьи и руководства по тестированию"),
        ("Ministry of Testing", "https://www.ministryoftesting.com", "Сообщество тестировщиков"),
        ("Selenium", "https://www.selenium.dev", "Документация по Selenium"),
    ],
    "Программирование": [
        ("GitHub", "https://github.com", "Хостинг кода и разработки"),
        ("Stack Overflow", "https://stackoverflow.com", "Вопросы и ответы"),
        ("MDN Web Docs", "https://developer.mozilla.org", "Документация по веб-технологиям"),
    ],
    "Data Science": [
        ("Kaggle", "https://www.kaggle.com", "Соревнования и датасеты"),
        ("Towards Data Science", "https://towardsdatascience.com", "Статьи по Data Science"),
        ("Google AI", "https://ai.google", "Исследования ИИ от Google"),
    ],
    "API": []  # Специальная категория для мемов
}

# Создание клавиатуры
def create_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Добавляем кнопки для IT ресурсов
    buttons = []
    for category in RESOURCES.keys():
        if category != "API":  # API добавим отдельно
            buttons.append(telebot.types.KeyboardButton(category))

    # Добавляем кнопки в два ряда
    markup.add(*buttons[:2])  # Первые две кнопки
    markup.add(*buttons[2:])  # Остальные кнопки
    markup.add(telebot.types.KeyboardButton("API"))
    markup.add(telebot.types.KeyboardButton("Закрыть клавиатуру"))

    return markup

# Создание убранной клавиатуры
def remove_keyboard():
    return telebot.types.ReplyKeyboardRemove()

# Функция для получения случайного мема с API
def get_random_meme():
    try:
        # Используем API для получения мемов (несколько вариантов на выбор)
        apis = [
            "https://meme-api.com/gimme",  # API с реддит мемами
            "https://api.imgflip.com/get_memes"  # API imgflip
        ]

        # Попробуем первый API
        response = requests.get(apis[0], timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Проверяем структуру ответа для первого API
            if 'url' in data:
                return {
                    'image_url': data['url'],
                    'title': data.get('title', 'Случайный мем'),
                    'source': 'Reddit'
                }
            elif 'data' in data and 'url' in data['data']:
                return {
                    'image_url': data['data']['url'],
                    'title': data['data'].get('title', 'Случайный мем'),
                    'source': 'Reddit'
                }

        # Если первый API не сработал, попробуем второй
        response = requests.get(apis[1], timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success'] and 'memes' in data['data']:
                import random
                meme = random.choice(data['data']['memes'])
                return {
                    'image_url': meme['url'],
                    'title': meme['name'],
                    'source': 'Imgflip'
                }

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON: {e}")

    # Если все API не сработали, вернем заглушку
    return {
        'image_url': 'https://i.imgflip.com/30b1gx.jpg',
        'title': 'Запасной мем',
        'source': 'Локальный'
    }

# Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    user_states[user_id] = {"name": None, "step": "ask_name"}

    bot.send_message(message.chat.id, "Здравствуй, я робот Чипалино, как вас зовут?")

# Обработка ввода имени
@bot.message_handler(func=lambda message: message.text and user_states.get(message.from_user.id, {}).get("step") == "ask_name")
def get_name(message):
    user_id = message.from_user.id
    user_name = message.text.strip()

    # Сохраняем имя пользователя
    user_states[user_id]["name"] = user_name
    user_states[user_id]["step"] = "ready"

    # Приветствуем и показываем клавиатуру
    bot.send_message(
        message.chat.id,
        f"Приятно познакомиться, {user_name}, предлагаю вам ознакомиться с данными ресурсами",
        reply_markup=create_keyboard()
    )

# Реакция на "Закрыть клавиатуру"
@bot.message_handler(func=lambda message: message.text == "Закрыть клавиатуру" and user_states.get(message.from_user.id, {}).get("step") == "ready")
def close_keyboard(message):
    user_name = user_states.get(message.from_user.id, {}).get("name", "друг")
    bot.send_message(
        message.chat.id,
        f"{user_name}, клавиатура скрыта. Напишите 'Открыть клавиатуру' чтобы вернуть её.",
        reply_markup=remove_keyboard()
    )

# Реакция на "Открыть клавиатуру"
@bot.message_handler(func=lambda message: message.text == "Открыть клавиатуру" and user_states.get(message.from_user.id, {}).get("step") == "ready")
def open_keyboard(message):
    user_name = user_states.get(message.from_user.id, {}).get("name", "друг")
    bot.send_message(
        message.chat.id,
        f"{user_name}, клавиатура открыта!",
        reply_markup=create_keyboard()
    )

# Реакция на кнопку "API" - отправка случайного мема
@bot.message_handler(func=lambda message: message.text == "API" and user_states.get(message.from_user.id, {}).get("step") == "ready")
def send_meme(message):
    user_name = user_states.get(message.from_user.id, {}).get("name", "друг")

    # Отправляем сообщение о загрузке
    loading_msg = bot.send_message(message.chat.id, f"{user_name}, загружаю мем...")

    try:
        # Получаем мем с API
        meme_data = get_random_meme()

        # Отправляем мем с описанием
        caption = f"🎲 Случайный мем\n📝 {meme_data['title']}\n🔗 Источник: {meme_data['source']}"

        # Пробуем отправить как фото
        bot.send_photo(
            message.chat.id,
            meme_data['image_url'],
            caption=caption
        )

        # Удаляем сообщение о загрузке
        bot.delete_message(message.chat.id, loading_msg.message_id)

    except Exception as e:
        # В случае ошибки
        bot.edit_message_text(
            f"❌ Ошибка при загрузке мема: {str(e)}",
            message.chat.id,
            loading_msg.message_id
        )

# Реакция на голосовые сообщения
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.reply_to(message, "Зачем ты мне это отправил, черт?")

# Реакция на аудио файлы
@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    bot.reply_to(message, "Аудио? Серьезно? Мне нужны кнопки, а не это!")

# Реакция на документы
@bot.message_handler(content_types=['document'])
def handle_document(message):
    bot.reply_to(message, "Не присылай мне файлы, я бот для ссылок!")

# Обработка нажатий кнопок (только когда пользователь представился)
@bot.message_handler(func=lambda message: message.text in RESOURCES.keys() and user_states.get(message.from_user.id, {}).get("step") == "ready" and message.text != "API")
def send_resources(message):
    category = message.text
    user_name = user_states.get(message.from_user.id, {}).get("name", "друг")

    response = f"<b>{category}:</b>\n\n"

    for name, url, desc in RESOURCES[category]:
        response += f"• <b>{name}</b>\n{desc}\n{url}\n\n"

    bot.send_message(message.chat.id, response, parse_mode='HTML')

# Обработка любых других сообщений (когда пользователь уже представился)
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("step") == "ready")
def handle_other_messages(message):
    # Пропускаем сообщения, которые уже обработаны другими хендлерами
    if (message.text in RESOURCES.keys() or 
        message.text == "Закрыть клавиатуру" or 
        message.text == "Открыть клавиатуру"):
        return

    # Если это не команда, не ресурс и не управление клавиатурой
    bot.reply_to(message, "Нажми на одну из кнопок или напиши 'Закрыть клавиатуру'/'Открыть клавиатуру'")

# Обработка сообщений от пользователей, которые еще не начали
@bot.message_handler(func=lambda message: True)
def handle_new_users(message):
    user_id = message.from_user.id
    if user_id not in user_states or user_states[user_id].get("step") != "ask_name":
        bot.send_message(message.chat.id, "Пожалуйста, начните с команды /start")

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    print("Добавлена новая кнопка 'API' для отправки случайных мемов!")
    bot.infinity_polling()