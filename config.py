import os

from dotenv import load_dotenv

load_dotenv()

CHECKER_IP_SITE = os.getenv('CHECKER_IP_SITE3')

LOGIN = os.getenv('LOGIN_2')
PASSWORD = os.getenv('PASSWORD_2')

PROXY_IP = os.getenv('PROXY_IP_2')
PROXY_LOG = os.getenv('PROXY_LOG_2')
PROXY_PASS = os.getenv('PROXY_PASS_2')

PROXY_PORT = os.getenv('PROXY_PORT_2')

URL = os.getenv('URL')
URL_GAME = URL + os.getenv('URL_GAME')
URL_MAIN = URL + os.getenv('URL_MAIN')
URL_EVENT = URL + os.getenv('URL_EVENT')

HOME_DIR = os.getenv('HOME_DIR')

FLOOR = os.getenv('FLOOR')

user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; \
rv:11.0) like Gecko"

HEADER = {'User-Agent': user_agent}

DATA = {
    'player_nick': LOGIN,
    'player_password': PASSWORD,
}

PROXYES = {
    "http": f"http://{PROXY_LOG}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}",
    "https": f"https://{PROXY_LOG}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}",
}
