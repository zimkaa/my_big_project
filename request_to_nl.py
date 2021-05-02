from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger
import os
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
    logger.add("requests.log", format="{time} {level} {message}",
               level="DEBUG", rotation="10 MB", compression="zip")
    now = datetime.now().strftime('%d-%m-%Y')
    name = f"{config.HOME_DIR}\\{now}.txt"
    if os.path.exists(os.path.join(os.getcwd(), name)):
        logger.error("I'am using cookies")
        string = ""
        with open(name, "r", encoding="cp1251") as data:
            for line in data:
                string += line
            dict2 = eval(string)
        for cookies in dict2:
            connect.cookies.set(**cookies)
        html = get_html(
            connect, config.URL_MAIN, config.HEADER, config.PROXYES,
        )
    else:
        logger.error("First loging for day")
        get_html(connect, config.URL, config.HEADER, config.PROXYES)
        post_html(
            connect, config.URL_GAME, config.HEADER,
            config.PROXYES, config.DATA,
        )
        cookies_dict = [
            {"domain": key.domain, "name": key.name, "path": key.path, "value": key.value}
            for key in connect.cookies
        ]
        make_file(str(cookies_dict), "cookies")
        html = get_html(
            connect, config.URL_MAIN, config.HEADER, config.PROXYES,
        )
    return html


def make_file(answer, name):
    """
    Сохраняем результат в файл для дальнейшей оценки
    """
    now = datetime.now().strftime('%d-%m-%Y')
    with open(f"{config.HOME_DIR}\\{now}.txt", "w", encoding="cp1251") as file:
        file.write(answer)
