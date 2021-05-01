from loguru import logger
import requests

import config
from game_play import game
from request_to_nl import log_in, set_session


logger.add("main.log", format="{time} {level} {message}", level="DEBUG",
           rotation="10 MB", compression="zip")


def my_ip(proxies=None):
    """
    Получаем текущий IP сессии
    """
    answer = requests.get(config.CHECKER_IP_SITE,
                          headers=config.HEADER, proxies=proxies)
    return answer.text


def main():
    ip = my_ip(config.PROXYES)
    logger.info(f"-------ip-------{ip}")
    if config.PROXY_IP in ip:
        logger.info("ip IS proxy YES")
        connect = set_session()
        html = log_in(connect)
        logger.info(game(connect, html))


if __name__ == '__main__':
    main()
