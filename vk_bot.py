import vk_api
import sqlite3
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from settings import token, admin_ids

vk_session = vk_api.VkApi(token=token)

longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

applications = {}

# Create table in db
def create_table():
    conn = sqlite3.connect('database_vk.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT NOT NULL, 
                       phone TEXT NOT NULL, 
                       description TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Send message to user
def send_message(user_id, message):
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=get_random_id(),
    )


# Message with buttons
def send_message_with_keyboard(user_id, message, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        message=message,
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id()
    )

# Send notification to administrators
def send_notification(admin_ids, message):
    for admin_id in admin_ids:
        send_message(admin_id, message)

# Main loop
for event in longpoll.listen():
    
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        message = event.text.lower()

        if event.from_user:
            
            if message == "оставить заявку":
                applications[user_id] = {}
                applications[user_id]["state"] = "name"
                send_message(user_id, "Как Вас зовут?")
            
            elif user_id in applications:
                
                if applications[user_id]["state"] == "name":
                    name = message
                    applications[user_id]["state"] = "phone"
                    send_message(user_id, "Введите Ваш номер телефона")
                
                elif applications[user_id]["state"] == "phone":
                    
                    if (len(message) == 11 and '+' not in message) or (len(message) == 12 and '+' in message):
                        phone_number = message
                        applications[user_id]["state"] = "description"
                        send_message(user_id, "Описание работ")
                    
                    else:
                        send_message(user_id, "Некорректный формат номера телефона. Пожалуйста, введите номер в формате 81234567890 или +71234567890")
                
                elif applications[user_id]["state"] == "description":
                    description = message
                    
                    # Сохранение данных в базе данных SQLite
                    conn = sqlite3.connect('database_vk.db')
                    create_table()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO requests (name, phone, description) VALUES (?, ?, ?)",
                                    (name, phone_number, description))            
                    conn.commit()
                    conn.close()
                    
                    # Отправка уведомления администраторам о новой заявке
                    admin_chats = admin_ids
                    notification_message = f"Новая заявка оформлена!\n\nИмя: {name.capitalize()}\n\nНомер телефона: {phone_number}\n\nОписание работ: {description.capitalize()}"
                    send_notification(admin_chats, notification_message)
                    
                    # Добавьте свою логику для обработки описания работ и сохранения заявки
                    send_message(user_id, f"Спасибо! Ваша заявка принята.\n\n Имя: {name.capitalize()}\n\n Номер телефона: {phone_number}\n\n Описание работ: {description.capitalize()}\n\n Для оформления новой заявки отправьте любое сообщение.")
                    
                    applications[user_id]["state"] = "completed"
                    
                    del applications[user_id]  # Сброс состояния после оформления заявки
            else:
                
                keyboard = VkKeyboard(inline=True)
                keyboard.add_button("Оставить заявку", color=VkKeyboardColor.POSITIVE)
                keyboard.add_openlink_button("Перейти в Telegram", link='https://t.me/afdcompany', payload=None)
                
                send_message_with_keyboard(user_id, "Здравствуйте!", keyboard)



