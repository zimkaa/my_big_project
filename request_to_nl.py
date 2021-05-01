from bs4 import BeautifulSoup
from datetime import datetime
import requests
import config


def set_session():
    """
    Создаем сессию
    """
    session = requests.Session()
    return session


def get_html(session, site_url, head=None, proxy=None, data=None):
    """
    Гет запрос
    """
    result = session.get(site_url, proxies=proxy, headers=head, params=data)
    return result


def post_html(session, site_url, head=None, proxy=None, data=None):
    """
    Пост запрос
    """
    result = session.post(site_url, proxies=proxy, headers=head, data=data)
    return result


def get_data(html):
    """
    Получаем объект супа
    """
    soup = BeautifulSoup(html.text, "html.parser")
    return soup


def my_ip(proxies=None):
    """
    Получаем текущий IP сессии
    """
    answer = requests.get(
        config.CHECKER_IP_SITE, headers=config.HEADER, proxies=proxies,
    )
    return answer.text


def log_in(connect):
    """
    Возвращает текст в виде джейсон текста после логина
    """
    get_html(connect, config.URL, config.HEADER, config.PROXYES)
    post_html(connect, config.URL_GAME, config.HEADER,
              config.PROXYES, config.DATA)
    html = get_html(connect, config.URL_MAIN, config.HEADER, config.PROXYES)
    # make_file(html.text, "log_in_main")
    return html


def make_file(answer, name):
    """
    Сохраняем результат в файл для дальнейшей оценки
    """
    now = datetime.now().strftime('%H-%M-%S')
    with open(f"{config.HOME_DIR}\\{now}_{name}.txt", "w", encoding="utf-8") as file:
        file.write(answer)
