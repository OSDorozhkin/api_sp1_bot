import logging
import os
import time

from dotenv import load_dotenv
import requests
import telegram

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filemode='w'
)

try:
    PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    if None in [PRAKTIKUM_TOKEN, TELEGRAM_TOKEN, CHAT_ID]:
        raise ValueError
except ValueError:
    logging.error('Получены не все переменные окружения.')

BASE_URL = 'https://praktikum.yandex.ru/'
AD_HW_STATUS_URL = 'api/user_api/homework_statuses/'
ANGRY = u'\U0001F620'
SMILE = u'\U0001F603'
MONKEY = u'\U0001F648'


def parse_homework_status(homework):
    homework_name = homework['lesson_name']
    if homework['status'] == 'reviewing':
        return f'Вашу работу "{homework_name}" начали проверять {MONKEY}.'
    if homework['status'] == 'rejected':
        verdict = (f'Отклонено {ANGRY}. '
                   f'Комментарий: {homework["reviewer_comment"]}')
    else:
        verdict = (f'Принято {SMILE}. '
                   f'Комментарий: {homework["reviewer_comment"]}')
    logging.info('Сообщение сформировано')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {
        'from_date': current_timestamp
    }
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }

    homework_statuses = requests.get('{}{}'.format(
        BASE_URL, AD_HW_STATUS_URL), params=params, headers=headers
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Бот запущен')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homeworks = new_homework.get('homeworks')
            if homeworks:
                homework = parse_homework_status(homeworks[0])
                send_message(homework, bot)
                logging.info('Сообщение отправлено')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(1200)
        except requests.exceptions.HTTPError as error:
            message = f'Ресурс недоступен: {error}'
            logging.error(message)
            send_message(message, bot)
        except requests.exceptions.ConnectionError as error:
            message = f'Обрыв соединения: {error}'
            logging.error(message)
            send_message(message, bot)
            time.sleep(1200)
        except KeyError:
            message = 'Данные от сервера не получены'
            logging.error(message)
            send_message(message, bot)


if __name__ == '__main__':
    main()
