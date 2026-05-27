from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from gigachat import GigaChat
from dotenv import load_dotenv


import random
import json
import os
import vk_api

from datetime import datetime

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')


GIGACHAT_TOKEN = os.getenv('GIGACHAT_TOKEN')
GIGACHAT_CREDENTIALS = GIGACHAT_TOKEN
GIGACHAT_SCOPE = 'GIGACHAT_API_PERS'

HISTORY_FILE = 'dialog_history.json'
STATS_FILE = 'stats.json'
USERS_FILE = 'users.json'
STATE_FILE = 'state.json'

SYSTEM_PROMPT = """
Ты — бот эмоциональной поддержки.

Правила:
1. Не называй себя психологом
2. Не ставь диагнозы
3. Отвечай естественно
4. Поддерживай пользователя
5. Отвечай кратко
6. Не используй смайлики
7. Если человеку тяжело — предложи обратиться за профессиональной помощью
"""

def get_help_contacts():
    """Возвращает текст с номерами телефонов доверия"""
    return """
⚠️ Вы не одни! Помните, что обращаться за помощью — это нормально.

📞 **Телефоны доверия (Россия):**

• Единый общероссийский телефон доверия: **8-800-2000-122** (круглосуточно, анонимно, бесплатно)

• МЧС России: **8-800-775-17-17** (психологическая помощь)

• Кризисная линия помощи: **8-800-100-19-19**

• Детский телефон доверия: **8-800-2000-122**

🌐 **Онлайн-помощь:**
• Чат психологической поддержки: psi.mchs.gov.ru

💙 **Помните:** Профессиональные психологи готовы вас выслушать и поддержать в любой ситуации.
"""

def is_critical_mood(mood, score):
    """Проверяет, находится ли пользователь в критическом состоянии"""
    critical_moods = ['Плохо', 'Очень плохо']
    critical_scores = [1, 2, 3]
    
    return mood in critical_moods or score in critical_scores

giga = GigaChat(
    credentials=GIGACHAT_CREDENTIALS,
    scope=GIGACHAT_SCOPE,
    verify_ssl_certs=False,
    model='GigaChat'
)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default


def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_new_user(user_id):
    users = load_json(USERS_FILE, {})
    return str(user_id) not in users


def register_user(user_id):
    users = load_json(USERS_FILE, {})

    if str(user_id) not in users:
        users[str(user_id)] = {
            'registered_at': datetime.now().isoformat(),
            'greeted': False 
        }

    save_json(USERS_FILE, users)


def is_greeted(user_id):
    """Проверяет, было ли уже приветствие"""
    users = load_json(USERS_FILE, {})
    user_data = users.get(str(user_id), {})
    return user_data.get('greeted', False)


def set_greeted(user_id):
    """Отмечает, что пользователь уже получил приветствие"""
    users = load_json(USERS_FILE, {})
    uid = str(user_id)
    
    if uid in users:
        users[uid]['greeted'] = True
        save_json(USERS_FILE, users)

def get_user_state(user_id):
    states = load_json(STATE_FILE, {})
    return states.get(str(user_id))


def set_user_state(user_id, data):
    states = load_json(STATE_FILE, {})
    states[str(user_id)] = data
    save_json(STATE_FILE, states)


def clear_user_state(user_id):
    states = load_json(STATE_FILE, {})

    if str(user_id) in states:
        del states[str(user_id)]

    save_json(STATE_FILE, states)

def main_keyboard():
    keyboard = VkKeyboard(one_time=False)

    keyboard.add_button(
        'Записать состояние',
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_line()

    keyboard.add_button(
        'Статистика',
        color=VkKeyboardColor.SECONDARY
    )

    keyboard.add_line()

    keyboard.add_button(
        'Поговорить',
        color=VkKeyboardColor.POSITIVE
    )

    return keyboard


def mood_keyboard():
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button(
        'Отлично',
        color=VkKeyboardColor.POSITIVE
    )

    keyboard.add_line()

    keyboard.add_button(
        'Хорошо',
        color=VkKeyboardColor.PRIMARY
    )

    keyboard.add_line()

    keyboard.add_button(
        'Нормально',
        color=VkKeyboardColor.SECONDARY
    )

    keyboard.add_line()

    keyboard.add_button(
        'Плохо',
        color=VkKeyboardColor.NEGATIVE
    )

    keyboard.add_line()

    keyboard.add_button(
        'Очень плохо',
        color=VkKeyboardColor.NEGATIVE
    )

    return keyboard

def send_message(user_id, text, keyboard=None):
    params = {
        'user_id': user_id,
        'message': text,
        'random_id': random.randint(1, 999999999)
    }

    if keyboard:
        params['keyboard'] = keyboard.get_keyboard()

    vk.messages.send(**params)

def add_history(user_id, user_text, bot_text):
    history = load_json(HISTORY_FILE, {})

    uid = str(user_id)

    if uid not in history:
        history[uid] = []

    history[uid].append({
        'user': user_text,
        'bot': bot_text,
        'time': datetime.now().isoformat()
    })

    history[uid] = history[uid][-10:]

    save_json(HISTORY_FILE, history)


def get_context(user_id):
    history = load_json(HISTORY_FILE, {})

    uid = str(user_id)

    if uid not in history:
        return ''

    text = ''

    for item in history[uid][-5:]:
        text += f"Пользователь: {item['user']}\n"
        text += f"Бот: {item['bot']}\n"

    return text

def save_mood(user_id, mood, score, reason):
    stats = load_json(STATS_FILE, {})

    uid = str(user_id)

    if uid not in stats:
        stats[uid] = []

    stats[uid].append({
        'mood': mood,
        'score': score,
        'reason': reason,
        'date': datetime.now().isoformat(),
        'critical': is_critical_mood(mood, score)
    })

    save_json(STATS_FILE, stats)


def get_stats(user_id):
    stats = load_json(STATS_FILE, {})

    uid = str(user_id)

    if uid not in stats:
        return 'Статистика пока отсутствует.'

    result = 'Ваша статистика:\n\n'

    for item in stats[uid][-10:]:

        result += (
            f"Состояние: {item['mood']}\n"
            f"Оценка: {item['score']}/10\n"
            f"Влияние: {item['reason']}\n"
            f"Дата: {item['date'][:10]}\n\n"
        )

    return result

def welcome_text():
    return """
Здравствуйте! 👋

Это бот эмоциональной поддержки.

Бот умеет:
• записывать ваше состояние
• показывать статистику  
• поддерживать диалог

⚠️ Важно: бот не заменяет профессиональную психологическую помощь.

Просто напишите мне сообщение, и я отвечу!
"""

def generate_response(user_id, message):
    context = get_context(user_id)

    prompt = f"""
{SYSTEM_PROMPT}

История диалога:
{context}

Пользователь: {message}
"""

    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content

    except Exception as e:
        print(e)
        return 'Произошла ошибка. Попробуйте позже.'

def process_message(user_id, text):

    if is_new_user(user_id):
        register_user(user_id)
        
        send_message(
            user_id,
            welcome_text(),
            main_keyboard()  
        )
        
        set_greeted(user_id)
        return

    if text.lower() == 'начать':
        send_message(
            user_id,
            welcome_text(),
            main_keyboard()
        )
        return

    if text == 'Записать состояние':
        send_message(
            user_id,
            'Как вы себя чувствуете?',
            mood_keyboard()
        )
        return

    if text == 'Статистика':
        send_message(
            user_id,
            get_stats(user_id),
            main_keyboard()
        )
        return

    if text == 'Поговорить':
        send_message(
            user_id,
            'Я слушаю вас. Расскажите, что вас беспокоит?',
            main_keyboard()
        )
        return

    moods = [
        'Отлично',
        'Хорошо',
        'Нормально',
        'Плохо',
        'Очень плохо'
    ]

    state = get_user_state(user_id)

    if text in moods:

        set_user_state(user_id, {
            'step': 'waiting_score',
            'mood': text
        })

        send_message(
            user_id,
            'Оцените состояние по шкале от 1 до 10 (где 1 - очень плохо, 10 - отлично).'
        )

        return

    if state and state.get('step') == 'waiting_score':

        if not text.isdigit():
            send_message(
                user_id,
                'Пожалуйста, введите число от 1 до 10.'
            )
            return

        score = int(text)

        if score < 1 or score > 10:
            send_message(
                user_id,
                'Оценка должна быть от 1 до 10.'
            )
            return

        state['score'] = score
        state['step'] = 'waiting_reason'

        set_user_state(user_id, state)

        send_message(
            user_id,
            'Что сейчас влияет на ваше состояние больше всего?'
        )

        return

    if state and state.get('step') == 'waiting_reason':

        reason = text
        mood = state['mood']
        score = state['score']

        save_mood(user_id, mood, score, reason)

        send_message(
            user_id,
            'Спасибо, я сохранил вашу запись.',
            main_keyboard()
        )

        if is_critical_mood(mood, score):
            send_message(
                user_id,
                get_help_contacts(),
                main_keyboard()
            )
            support_message = (
                "Я вижу, что вам сейчас непросто. "
                "Пожалуйста, помните, что вы не одни. "
                "Профессионалы готовы вас выслушать и поддержать."
            )
            send_message(user_id, support_message, main_keyboard())

        clear_user_state(user_id)

        return

    reply = generate_response(user_id, text)

    send_message(
        user_id,
        reply,
        main_keyboard()
    )

    add_history(user_id, text, reply)

print('Бот эмоциональной поддержки запущен')
print('Ожидание сообщений...')

for event in longpoll.listen():

    if event.type == VkEventType.MESSAGE_NEW and event.to_me:

        user_id = event.user_id
        text = event.text.strip()

        print(f'Сообщение от {user_id}: {text}')

        process_message(user_id, text)