import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === Налаштування ===
TOKEN = '7617891900:AAHtNNOED6qNFI3pNxttfreqo3RA6UMgctk'
GROUP_CHAT_ID = -1002862196775  # Введи свій ID групи

bot = telebot.TeleBot(TOKEN)

# Зберігаємо замовлення
orders = {}
awaiting_sum = {}  # тимчасове збереження хто вводить суму і до якого замовлення

# Додавання замовлення
@bot.message_handler(commands=['add'])
def handle_add(message):
    if message.chat.type == 'private':
        order_text = message.text[len('/add '):].strip()
        if not order_text:
            bot.send_message(message.chat.id, "❗ Введіть текст замовлення після /add")
            return

        msg = bot.send_message(
            GROUP_CHAT_ID,
            f"🆕 <b>Нове замовлення</b>\n\n{order_text}",
            parse_mode="HTML",
            reply_markup=order_keyboard()
        )
        orders[msg.message_id] = {
            "text": order_text,
            "status": "нове",
            "taken_by": None
        }
        bot.send_message(message.chat.id, "✅ Замовлення опубліковане")

# Кнопки
def order_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Взяти в роботу", callback_data="take"))
    return markup

def done_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Виконано", callback_data="done"))
    return markup

def sum_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💵 Сума замовлення", callback_data="sum"))
    return markup

# Обробка кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    message_id = call.message.message_id
    user = call.from_user
    order = orders.get(message_id)

    if not order:
        bot.answer_callback_query(call.id, "❗ Замовлення не знайдено.")
        return

    if call.data == "take":
        if order["status"] != "нове":
            bot.answer_callback_query(call.id, "Це замовлення вже в роботі або виконано.")
            return

        order["status"] = "в роботі"
        order["taken_by"] = user.id

        updated_text = f"🛠 <b>В роботі</b>\n\n{order['text']}\n👨‍🔧 Майстер: {user.first_name}"
        bot.edit_message_text(updated_text, GROUP_CHAT_ID, message_id, parse_mode="HTML", reply_markup=done_keyboard())
        bot.answer_callback_query(call.id, "Замовлення взято в роботу.")

    elif call.data == "done":
        if order["status"] != "в роботі" or order["taken_by"] != user.id:
            bot.answer_callback_query(call.id, "Тільки майстер, який взяв замовлення, може завершити його.")
            return

        order["status"] = "виконано"
        updated_text = (
            f"✅ <b>Замовлення виконано</b>\n\n"
            f"{order['text']}\n"
            f"👨‍🔧 Майстер: {user.first_name}"
        )
        bot.edit_message_text(updated_text, GROUP_CHAT_ID, message_id, parse_mode="HTML", reply_markup=sum_keyboard())
        bot.answer_callback_query(call.id, "Замовлення позначено як виконане.")

    elif call.data == "sum":
        if order["status"] != "виконано" or order["taken_by"] != user.id:
            bot.answer_callback_query(call.id, "❗ Ви не можете вказати суму для цього замовлення.")
            return

        awaiting_sum[user.id] = message_id  # запам’ятовуємо, що користувач має ввести суму
        bot.send_message(GROUP_CHAT_ID, f"{user.first_name}, 💬 Введіть суму замовлення (наприклад: 790 грн):")
        bot.answer_callback_query(call.id)

# Обробка введення суми в групі
@bot.message_handler(func=lambda message: message.chat.id == GROUP_CHAT_ID)
def handle_group_message(message):
    user_id = message.from_user.id

    if user_id in awaiting_sum:
        message_id = awaiting_sum.pop(user_id)
        order = orders.get(message_id)
        if order:
            sum_text = message.text.strip()
            updated_text = (
                f"✅ <b>Замовлення закрито</b>\n\n"
                f"{order['text']}\n"
                f"👨‍🔧 Майстер: {message.from_user.first_name}\n"
                f"💵 Сума: {sum_text}"
            )
            bot.edit_message_text(updated_text, GROUP_CHAT_ID, message_id, parse_mode="HTML")
            bot.reply_to(message, "✅ Сума додана, замовлення закрито.")

# Запуск
print("Бот запущено...")
bot.infinity_polling()
