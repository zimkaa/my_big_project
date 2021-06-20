from bs4 import BeautifulSoup  # type: ignore
from datetime import datetime
import requests

# from loguru import logger

import config


def send_telegram(text: str) -> None:
    token = config.TG_TOKEN  # type: ignore
    url = "https://api.telegram.org/bot"
    channel_id = config.CHANNEL_ID  # type: ignore
    url += token  # type: ignore
    method = url + "/sendMessage"  # type: ignore
    query = requests.post(
        method,
        data={
            "chat_id": channel_id,  # type: ignore
            "text": text,  # type: ignore
        },
    )
    if query.status_code != 200:
        raise Exception("Some trouble with TG")


def my_ip(proxies: dict = None) -> str:
    """
    Get IP (need to chek proxye)
    """
    answer = requests.get(
        config.CHECKER_IP_SITE,
        headers=config.HEADER, proxies=proxies)  # type: ignore
    if answer.status_code != 200:
        text = "PROXY DON'T RESPONSE!!!"
        send_telegram(text)
        raise Exception(text)
    return answer.text


def set_session() -> requests.sessions.Session:
    """
    Создаем сессию
    """
    session = requests.Session()
    session.proxies.update(config.PROXYES)
    session.headers.update(config.HEADER)
    return session


def get_html(session: requests.sessions.Session, site_url: str, head=None,
             proxy=None, data: dict = None) -> requests.models.Response:
    """
    Executing a get request
    """
    try:
        result = session.get(site_url, params=data)
    except Exception:
        text = "----PROXY CRASH----"
        send_telegram(text)
        raise Exception(text)
    return result


def post_html(session: requests.sessions.Session, site_url: str, head=None,
              proxy=None, data: dict = None) -> requests.models.Response:
    """
    Executing a post request
    """
    try:
        result = session.post(site_url, data=data)
    except Exception:
        text = "----PROXY CRASH----"
        send_telegram(text)
        raise Exception(text)
    return result


def get_data(html: requests.models.Response) -> BeautifulSoup:
    """
    Получаем объект супа
    """
    soup = BeautifulSoup(html.text, "html.parser")
    return soup


def log_in(my_connect: requests.Session) -> requests.models.Response:
    """
    Loggin to game
    """
    get_html(my_connect, config.URL, config.HEADER, config.PROXYES)
    post_html(
        my_connect, config.URL_GAME, config.HEADER,
        config.PROXYES, config.DATA)  # type: ignore
    html = get_html(
        my_connect, config.URL_MAIN, config.HEADER, config.PROXYES,
    )
    return html


def make_file(text: str) -> None:
    """
    Write data to file
    """
    now = datetime.now().strftime('%d-%m-%Y')
    with open(f"{config.HOME_DIR}\\{now}.txt", "w", encoding="cp1251") as file:
        file.write(text)
