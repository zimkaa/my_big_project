import os

from dotenv import load_dotenv

load_dotenv()

CHECKER_IP_SITE = os.getenv('CHECKER_IP_SITE')

LOGIN = os.getenv('LOGIN_3')
PASSWORD = os.getenv('PASSWORD_3')

PROXY_IP = os.getenv('PROXY_IP_3')
PROXY_LOG = os.getenv('PROXY_LOG_3')
PROXY_PASS = os.getenv('PROXY_PASS_3')

PROXY_PORT = os.getenv('PROXY_PORT_3')

URL = os.getenv('URL')
URL_GAME = URL + os.getenv('URL_GAME')
URL_MAIN = URL + os.getenv('URL_MAIN')
URL_EVENT = URL + os.getenv('URL_EVENT')

HOME_DIR = os.getenv('HOME_DIR')

FLOOR = os.getenv('FLOOR')

HEADER = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/\
        537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
}

DATA = {
    'player_nick': LOGIN,
    'player_password': PASSWORD
}

PROXYES = {
    "http": f"http://{PROXY_LOG}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}",
    "https": f"https://{PROXY_LOG}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}"
}
