from loguru import logger

import config
from game_play import game
from request_to_nl import log_in, set_session, my_ip


logger.add("main.log", format="{time} {level} {message}", level="DEBUG",
           rotation="10 MB", compression="zip")


def main():
    ip = my_ip(config.PROXYES)
    logger.info("\n")
    logger.info(f"-------ip-------{ip}")
    if config.PROXY_IP in ip:
        logger.info("ip IS proxy YES")
        connect = set_session()
        html = log_in(connect)
        result = game(connect, html)
        logger.info(result)


if __name__ == '__main__':
    main()
