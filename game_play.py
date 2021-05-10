from decimal import Decimal
import collections
import json
import re
from time import sleep

from loguru import logger

import config
# from fight import fighting
# from fight_dangeon_24 import fighting
from fight_dangeon_23_warrior import fighting
from request_to_nl import get_html, post_html, get_data


# logger.add("game_play.log", format="{time} {level} {message}", level="DEBUG",
#            rotation="1 day", compression="zip")


REVERSE_WAYS = {
    'moveUp': "moveDown",
    'moveRight': "moveLeft",
    'moveDown': "moveUp",
    'moveLeft': "moveRight",
}

REVERSE_WAYS_SHORT = {
    'u': "d",
    'r': "l",
    'd': "u",
    'l': "r",
}

NAME_WAY = {
    'moveUp': "u",
    'moveRight': "r",
    'moveDown': "d",
    'moveLeft': "l",
    '': "None",
}

CHANGE_NAME = {
    "moveDown": "openDown",
    "moveLeft": "openLeft",
    "moveUp": "openUp",
    "moveRight": "openRight",
}

CHANGE_NAME_PORT = {
    "openDown": "moveDown",
    "openLeft": "moveLeft",
    "openUp": "moveUp",
    "openRight": "moveRight",
}


def string_info(js_obj):
    """
    Create string to debug log
    """
    coord_x = js_obj['s']['x']
    coord_y = js_obj['s']['y']
    way_to_go = js_obj['s']['map'][js_obj['s']['x']][js_obj['s']['y']].get('p')
    oil = is_oil(js_obj)
    oil_price = js_obj['s']['oilPrice']
    floor = is_floor(js_obj)
    text = f"oil- '{oil}' oilPrice- '{oil_price}' floor- '{floor}' \
        x= '{coord_x}' y= '{coord_y}' '{way_to_go}'"
    return text


@logger.catch()
def ways_to_door(connect, js_obj, way: str):
    """
    Идем до двери так же нападаем и поднимаем все
    """
    if js_obj['a'].get(way):
        logger.info(f"----------moving to door------ '{way.upper()}'")
        text = string_info(js_obj)
        logger.info(text)
        vcode = js_obj['a'].get(way)
        first_part = r"^[a-z]+[^A-Z]"
        [action] = re.findall(first_part, way)
        second_part = r"[A-Z][a-z]+"
        [direction] = re.findall(second_part, way)
        # url = config.URL_EVENT + "?type=dungeon"
        # url += f"&action={action}&direction={direction.lower()}&vcode={vcode}"
        # html = post_html(connect, url, config.HEADER, config.PROXYES)
        data = {
            "type": "dungeon",
            "action": action,
            "direction": direction.lower(),
            "vcode": vcode,
        }
        html = post_html(connect, config.URL_EVENT,
                         config.HEADER, config.PROXYES, data)
        sleep(5.5)
        js_obj = check_pickup(connect, json.loads(html.text))
        if js_obj['a'].get('attack'):
            """
            Поднимаем ХП
            """
            html = get_html(connect, config.URL_MAIN,
                            config.HEADER, config.PROXYES)
            healing = 0.99
            js_obj = restoring_mana_and_hp(connect, html, healing)

            js_obj = is_attack(connect, js_obj)
    else:
        # logger.debug(f"-----door-----NO CELL TO MOVING!!! DON'T UNDERSTAND \
        #     WHY------'{way.upper()}'")
        # text = string_info(js_obj)
        # logger.debug(text)
        error = Exception("Boss!!!")
        raise error
    return js_obj


@logger.catch()
def ways_to_port(connect, js_obj, way: str):
    """
    Идем до портала
    """
    if js_obj['a'].get(way):
        logger.info(f"----------moving to port------'{way.upper()}'")
        text = string_info(js_obj)
        logger.info(text)
        vcode = js_obj['a'].get(way)
        first_part = r"^[a-z]+[^A-Z]"
        [action] = re.findall(first_part, way)
        second_part = r"[A-Z][a-z]+"
        [direction] = re.findall(second_part, way)
        # url = config.URL_EVENT + "?type=dungeon"
        # url += f"&action={action}&direction={direction.lower()}&vcode={vcode}"
        # html = post_html(connect, url, config.HEADER, config.PROXYES)
        data = {
            "type": "dungeon",
            "action": action,
            "direction": direction.lower(),
            "vcode": vcode,
        }
        html = post_html(connect, config.URL_EVENT,
                         config.HEADER, config.PROXYES, data)
        sleep(5.5)
        js_obj = check_pickup(connect, json.loads(html.text))
    else:
        error = Exception("Wrong-way to port")
        raise error
    return js_obj


@logger.catch()
def ways_to_go(connect, js_obj, way: str):
    """
    Идем в заданную сторону поднимаем вещи и бьем ботов или
    возвращаем сам объект
    """
    if js_obj['a'].get(way):
        logger.info(f"----------moving to------'{way.upper()}'")
        text = string_info(js_obj)
        logger.info(text)
        vcode = js_obj['a'].get(way)
        first_part = r"^[a-z]+[^A-Z]"
        [action] = re.findall(first_part, way)
        second_part = r"[A-Z][a-z]+"
        [direction] = re.findall(second_part, way)
        # url = config.URL_EVENT + "?type=dungeon"
        # url += f"&action={action}&direction={direction.lower()}&vcode={vcode}"
        # html = post_html(connect, url, config.HEADER, config.PROXYES)
        data = {
            "type": "dungeon",
            "action": action,
            "direction": direction.lower(),
            "vcode": vcode,
        }
        html = post_html(connect, config.URL_EVENT,
                         config.HEADER, config.PROXYES, data)
        sleep(5.5)
        js_obj = check_pickup(connect, json.loads(html.text))
        if js_obj['a'].get('attack'):
            """
            Поднимаем ХП
            """
            html = get_html(connect, config.URL_MAIN,
                            config.HEADER, config.PROXYES)
            healing = 0.10
            js_obj = restoring_mana_and_hp(connect, html, healing)

            js_obj = is_attack(connect, js_obj)

        # js_obj = is_attack(connect, json.loads(html.text))
    else:
        logger.info(f"-----go-----NO CELL TO MOVING------ \
            '{way.upper()}' ----------I THINK IT'S DOOR------")
        text = string_info(js_obj)
        logger.info(text)
        return js_obj
    return js_obj


def restoring_mana_and_hp(connect, html, healing):
    soup = get_data(html)
    elementos = soup.find(language="JavaScript")
    text = str(elementos).split('\n')
    inshp = text[2].replace('var inshp = ', '').replace('];', '')\
        .replace('[', '').split(",")
    my_max_hp = Decimal(inshp[1])
    my_max_mp = Decimal(inshp[3])
    my_hp = Decimal(inshp[0])
    my_mp = Decimal(inshp[2])
    # min_hp = my_max_hp * Decimal(0.99)
    # min_mp = my_max_mp * Decimal(0.99)
    min_hp = my_max_hp * Decimal(healing)
    min_mp = my_max_mp * Decimal(healing)
    count_hp = 0
    count_mp = 0
    if my_hp <= min_hp:
        count_hp = Decimal((min_hp - my_hp) / 100).quantize(Decimal('1'))
    if my_mp <= min_mp:
        count_mp = Decimal((min_mp - my_mp) / 100).quantize(Decimal('1'))
    if count_hp >= count_mp:
        count = count_hp
    else:
        count = count_mp
    # 309 --- Зелье Энергии
    # logger.error(f"count {count}")
    if count:
        logger.error(f"count {count}")
        js_obj = get_satatus(connect, html)
        for _ in range(int(count)):
            # key = "useWeapon.w27_521"  # BIG MP!!!
            key = "useWeapon.w27_309"  # 309 --- Зелье Энергии
            js_obj['a'][key]
            item = key.replace('useWeapon.', '')
            vcode = js_obj['a'].get(key)
            # url_part = f"?type=dungeon&action=useWeapon&item={item}&vcode={vcode}"
            # url = config.URL_EVENT + url_part
            # html = post_html(connect, url, config.HEADER, config.PROXYES)
            data = {
                "type": "dungeon",
                "action": "useWeapon",
                "item": item,
                "vcode": vcode,
            }
            html = post_html(connect, config.URL_EVENT, config.HEADER, config.PROXYES, data)
            # logger.error("use weapon useWeapon.w27_521 BIG MP!!!")
            logger.error("use weapon useWeapon.w27_309 potion energy!!!")
            js_obj = json.loads(html.text)
    else:
        logger.error(f"not count {count}")
        js_obj = get_satatus(connect, html)
    # return html
    return js_obj


def is_attack(connect, js_obj):
    """
    Если есть враги атакуем иначе возвращаем сам объект
    """
    # logger.debug(f"js_obj {js_obj}")
    if js_obj['a'].get('attack'):
        vcode = js_obj['a'].get('attack')
        url = config.URL_EVENT
        # url += f"?type=dungeon&action=attack&vcode={vcode}"
        # html = post_html(connect, url, config.HEADER, config.PROXYES)
        data = {
            "type": "dungeon",
            "action": "attack",
            "vcode": vcode,
        }
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        html = get_html(connect, config.URL_MAIN,
                        config.HEADER, config.PROXYES)
        html = fighting(connect, html)

        ####

        js_obj = get_satatus(connect, html)
        js_obj = check_pickup(connect, js_obj)
        js_obj = check_pickup(connect, js_obj)
        return js_obj
    else:
        js_obj = check_pickup(connect, js_obj)
        js_obj = check_pickup(connect, js_obj)
        return js_obj


def go_to_next_level(connect, js_obj):
    """
    Перемещаемся на левел ниже
    """
    logger.info("-----------------RUN go_to_next_level-------------------")
    if js_obj['a'].get('moveDeep'):
        vcode = js_obj['a'].get('moveDeep')
        url = config.URL_EVENT
        # url += f"?type=dungeon&action=moveDeep&vcode={vcode}"
        # html = post_html(connect, url, config.HEADER, config.PROXYES)
        data = {
            "type": "dungeon",
            "action": "moveDeep",
            "vcode": vcode,
        }
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        sleep(5.5)
        logger.info("--------NEXT LEVEL---------")
        return json.loads(html.text)
    else:
        logger.debug(f"-------can't activate portal-------\n{js_obj}")
        return js_obj


def check_pickup(connect, js_obj):
    """
    Поднимаем или нажимаем на вещь, сундук тоже считается поднятием.
    """
    for key in js_obj['a'].keys():
        if key.find("pickup") != -1:
            item = key.replace('pickup.', '')
            vcode = js_obj['a'].get(key)
            # url_part = f"?type=dungeon&action=pickup&item={item}&vcode={vcode}"
            # url = config.URL_EVENT + url_part
            # html = post_html(connect, url, config.HEADER, config.PROXYES)
            data = {
                "type": "dungeon",
                "action": "pickup",
                "item": item,
                "vcode": vcode,
            }
            html = post_html(connect, config.URL_EVENT,
                             config.HEADER, config.PROXYES, data)
            logger.info('pick up something')
            return json.loads(html.text)
    return js_obj


def parse_dungeon(soup):
    """
    Получаем ссылку на стату чтобы в будущем получать только JSON
    """
    elementos = soup.find(language="JavaScript")
    text = str(elementos).split('\n')
    var_obj_actions = text[9].replace('var objActions = ', '').replace(';', '')
    actions = json.loads(var_obj_actions)
    # return f"?type=dungeon&action=getStatus&vcode={actions.get('getStatus')}"
    data = {
        "type": "dungeon",
        "action": "getStatus",
        "vcode": actions.get('getStatus'),
    }
    return data


def get_satatus(connect, html):
    """
    Получаем статус (удобный способ получать только JSON данные)
    """
    soup = get_data(html)
    status_url = config.URL_EVENT
    # status_url += parse_dungeon(soup)
    # html = post_html(connect, status_url, config.HEADER, config.PROXYES)
    data = parse_dungeon(soup)
    html = post_html(connect, status_url, config.HEADER, config.PROXYES, data)
    return json.loads(html.text)


def go_to_this_cell(variant):
    """
    Перевожу в полное слово
    """
    var_dict = {
        'u': "moveUp",
        'r': "moveRight",
        'd': "moveDown",
        'l': "moveLeft",
    }
    return var_dict[variant]


def get_my_coord(js_obj):
    """
    Получаю свои координаты и варианты хода
    """
    my_coord = dict()
    my_coord['x'] = js_obj['s']['x']
    my_coord['y'] = js_obj['s']['y']
    my_coord['p'] = js_obj['s']['map'][js_obj['s']['x']][js_obj['s']['y']].get('p')
    return my_coord


def create_map():
    """
    Создаем пустые карты
    """
    map_to = [
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""]
    ]
    return map_to


# def is_open_door(js_obj, open_door):
#     dangeon_map = js_obj['s']['map']
#     for row_x in dangeon_map:
#         for data_cell in row_x:
#             if data_cell['doors']:
#                 for _, is_open in data_cell['doors'].items():
#                     if is_open == 0:
#                         open_door = True
#     return open_door


def add_way_port(map_port: list, my_coord: dict, to_move: str) -> list:
    """
    Добавляет направление движения если нет на этой клетке.
    """
    if not map_port[my_coord['x']][my_coord['y']]:
        map_port[my_coord['x']][my_coord['y']] = to_move
        logger.info(f"portal found. add way to port '{to_move}'")
    # else:
    #     logger.info(f"portal found {text}reverse way to port \
    #         already exists '{to_move}'")
    else:
        logger.info("portal found")
    return map_port


# @logger.catch()
def go_to_door(connect, js_obj, map_to_door: dict, map_to_port: dict):
    """
    Цикл похода до двери и вход в нее
    """
    logger.info("RUN go_to_door -----------------------------------------")
    stop = False
    old_variant = []
    while not stop:
        my_coord = get_my_coord(js_obj)
        variant = map_to_door[my_coord['x']][my_coord['y']]
        if js_obj['s']['doors']:
            for move, is_open in js_obj['s']['doors'].items():
                if is_open == 1:
                    rename_move = go_to_this_cell(move)
                    variant = CHANGE_NAME[rename_move]
                    logger.info("door closed. opening")
                    js_obj = ways_to_door(connect, js_obj, variant)
                    my_coord = get_my_coord(js_obj)
                    variant = map_to_door[my_coord['x']][my_coord['y']]
                elif is_open == 0:
                    # open_door = True
                    logger.debug("door open")
        old_variant.append(variant)
        if variant:
            # logger.info(f"i go to door my_coord - '{my_coord}' \
            #     variant to go to door - '{variant}'")
            js_obj = ways_to_door(connect, js_obj, variant)
            if len(old_variant) >= 2:
                to_move = REVERSE_WAYS[old_variant[-2]]
            else:
                to_move = REVERSE_WAYS[variant]
            map_to_port = add_way_port(map_to_port, my_coord, to_move)
            # to_move = REVERSE_WAYS[variant]
            # if not map_to_port[my_coord['x']][my_coord['y']]:
            #     map_to_port[my_coord['x']][my_coord['y']] = to_move
            #     logger.info(f"portal found add way to port {to_move}")
            # else:
            #     logger.info(f"portal found reverse way to portal already exists '{to_move}'")
        else:
            stop = True
            to_move = go_to_this_cell(my_coord['p'])
            map_to_port = add_way_port(map_to_port, my_coord, to_move)
            # if not map_to_port[my_coord['x']][my_coord['y']]:
            #     map_to_port[my_coord['x']][my_coord['y']] = to_move
            #     logger.info(f"i am into the door add way to port {to_move}")
            # else:
            #     logger.info(f"i am into the door reverse way to portal already exists '{to_move}'")
    return js_obj


def go_to_port(connect, js_obj, map_to_port: dict):
    """
    Цикл похода до портала
    """
    logger.info("RUN go_to_port --------------------")
    stop = False
    while not stop:
        my_coord = get_my_coord(js_obj)
        variant = map_to_port[my_coord['x']][my_coord['y']]
        logger.info(f"my_coord now- '{my_coord}' variant to port- '{variant}'")
        if variant == 'No':
            logger.info("i am into the portal")
            stop = True
        else:
            js_obj = ways_to_port(connect, js_obj, variant)
            # logger.info(f"i go to portal my_coord - '{my_coord}' variant to go to portal - '{variant}'")
    return js_obj


def go_to_next_cell(my_coord: dict, map_to_go: dict, delete_move=None):
    """
    Вычисляется вариант движения (в приоритете неизведанная клетка)
     и вариант возврата
    """
    if not map_to_go[my_coord['x']][my_coord['y']]:
        map_to_go[my_coord['x']][my_coord['y']] = {'p': my_coord['p']}
    if not map_to_go[my_coord['x']][my_coord['y']].get('r'):
        reverse = {'r': delete_move}
        map_to_go[my_coord['x']][my_coord['y']].update(reverse)
    logger.info(f"variants - '{map_to_go[my_coord['x']][my_coord['y']]['p']}'")
    variants = map_to_go[my_coord['x']][my_coord['y']]['p']
    if not variants:
        variants = map_to_go[my_coord['x']][my_coord['y']]['r']
        logger.info(f"reverse variants - '{variants}'")
    if len(variants) == 1:
        variant = variants
        # if variant == 'u':
        #     map_to_go[my_coord['x']][my_coord['y']]['p'] = variant.replace(variants, '')
        # elif variant == 'r':
        #     map_to_go[my_coord['x']][my_coord['y']]['p'] = variant.replace(variants, '')
        # elif variant == 'd':
        #     map_to_go[my_coord['x']][my_coord['y']]['p'] = variant.replace(variants, '')
        # else:
        #     map_to_go[my_coord['x']][my_coord['y']]['p'] = variant.replace(variants, '')
        map_to_go[my_coord['x']][my_coord['y']]['p'] = ''
        delete_move = REVERSE_WAYS_SHORT[variant]
    elif len(variants) == 2:
        if delete_move:
            if delete_move in variants:
                logger.info(f"delete_move in variants '{delete_move}' - '{variants}'")
                variants = variants.replace(delete_move, '')
                map_to_go[my_coord['x']][my_coord['y']]['p'] = variants
            else:
                logger.info(f"delete_move not in variants '{delete_move}' - '{variants}'")
        variant = variants[0]
        logger.info(f"variant to go - '{variant}'")
        if variant == 'u':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'r':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'd':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        else:
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        delete_move = REVERSE_WAYS_SHORT[variant]
    elif len(variants) == 3:
        if delete_move:
            if delete_move in variants:
                logger.info(f"delete_move in variants '{delete_move}' - '{variants}'")
                variants = variants.replace(delete_move, '')
                map_to_go[my_coord['x']][my_coord['y']]['p'] = variants
            else:
                logger.info(f"delete_move not in variants '{delete_move}' - '{variants}'")
        variant = variants[0]
        logger.info(f"variant to go - '{variant}'")
        if variant == 'u':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'r':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'd':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        else:
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        delete_move = REVERSE_WAYS_SHORT[variant]
    else:
        if delete_move:
            if delete_move in variants:
                logger.info(f"delete_move in variants '{delete_move}' - '{variants}'")
                variants = variants.replace(delete_move, '')
                map_to_go[my_coord['x']][my_coord['y']]['p'] = variants
            else:
                logger.info(f"delete_move not in variants '{delete_move}' - '{variants}'")
        else:
            map_to_go[my_coord['x']][my_coord['y']]['p'] = variants
        variant = variants[0]
        logger.info(f"variant to go - '{variant}'")
        if variant == 'u':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'r':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        elif variant == 'd':
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        else:
            now_cell = map_to_go[my_coord['x']][my_coord['y']]['p']
            map_to_go[my_coord['x']][my_coord['y']]['p'] = now_cell.replace(variant, '')
        delete_move = REVERSE_WAYS_SHORT[variant]
    way = go_to_this_cell(variant)
    return {'way': way, 'delete_move': delete_move}


def next_step(js_obj, map_to_go: list, delete_move: str) -> dict:
    """
    Вычисляем движение и обратный вариант
    """
    my_coord = get_my_coord(js_obj)
    logger.info(f"my_coord - '{my_coord}'")
    way = go_to_next_cell(my_coord, map_to_go, delete_move)
    return way


def check_key(js_obj, key: bool) -> bool:
    """
    Проверяем найден ли ключ
    """
    if not key:
        if js_obj['s']['own']:
            key = True
            logger.info("key found")
    else:
        logger.info("key found")
    return key


def check_portal(js_obj, portal: bool, map_to_port: list, way: str) -> dict:
    """
    Проверяем найден ли портал и записываем ход к порталу
    """
    if not portal:
        if js_obj['s'].get('portal'):
            """ на карте "v":11  """
            portal = True
            my_coord = get_my_coord(js_obj)
            # add_way_portal = {'x': my_coord['x'], 'y': my_coord['y'], 'p': 'No'}
            logger.info(f"portal - '{portal}'")
            # map_to_port.append(add_way_portal)
            to_move = "No"
            map_to_port = add_way_port(map_to_port, my_coord, to_move)
            # map_to_port[add_way_portal['x']][add_way_portal['y']] = add_way_portal['p']
    else:
        # logger.info(f"way['old_coord'] - {way['old_coord']}")
        # way_name = go_to_this_cell(way['delete_move'])
        # add_way_portal = {'x': js_obj['s']['x'], 'y': js_obj['s']['y'], 'p': way_name}
        # # if map_to_port[-1]['x'] == js_obj['s']['x'] and map_to_port[-1]['y'] == js_obj['s']['y']:
        # if map_to_port[add_way_portal['x']][add_way_portal['y']]:
        #     text_to_print = " reverse way to portal already exists"
        # else:
        #     text_to_print = f"add to map_to_port {add_way_portal}"
        #     # map_to_port.append(add_way_portal)
        #     map_to_port[add_way_portal['x']][add_way_portal['y']] = add_way_portal['p']
        # logger.info(f"portal found {text_to_print}")
        # logger.info("portal found")
        my_coord = get_my_coord(js_obj)
        to_move = go_to_this_cell(way['delete_move'])
        map_to_port = add_way_port(map_to_port, my_coord, to_move)
    return {'portal': portal, 'map_to_port': map_to_port}


def check_buttons(js_obj, buttons: bool) -> bool:
    """
    Проверяем нажаты ли все кнопки
    """
    if not buttons:
        number = js_obj['s'].get('buttonsLeft')
        if number == 0:
            buttons = True
            logger.info(f"buttons - '{buttons}' buttonsLeft - '{number}'")
    else:
        logger.info("buttons found")
    return buttons


def add_way_door(map_door: list, my_coord: dict, to_move: str) -> list:
    # map_door[my_coord['x']][my_coord['y']] = to_move
    # logger.info(f"door found. add way to door {to_move}")
    if not map_door[my_coord['x']][my_coord['y']]:
        map_door[my_coord['x']][my_coord['y']] = to_move
        logger.info(f"door found. add way to door '{to_move}'")
    else:
        logger.info("door found. reverse way already exists")
    return map_door


def check_doors(js_obj, doors, map_to_door, way, buttons, portal, key):
    """
    Проверяем дверь и так же открываем ее с записью в карту к двери
    """
    my_coord = get_my_coord(js_obj)
    if not doors:
        if js_obj['s']['doors']:
            logger.info("door found  ----------")
            doors = True
            for door_way, _ in js_obj['s']['doors'].items():
                if NAME_WAY[way['way']] == door_way:
                    if key:
                        text_to_print = f"script wants go to the \
                            door '{way['way']}'"
                        way['way'] = CHANGE_NAME[way['way']]
                        logger.debug(f"{text_to_print} change way name \
                            and just open door '{way['way']}'")
                # to_door_move = go_to_this_cell(door_way)
                # add_way_to_door = {'x': my_coord['x'], 'y': my_coord['y'], 'p': to_door_move}
                # map_to_door[my_coord['x']][my_coord['y']] = add_way_to_door['p']
                # logger.info(f"door_way on this cell is '{door_way}' \
                #     add to map_to_door '{add_way_to_door}'")
                to_move = go_to_this_cell(door_way)
                map_to_door = add_way_door(map_to_door, my_coord, to_move)
    else:
        if (buttons and portal) and key:
            # logger.info(f"------- way['delete_move'] '{way['delete_move']}'")
            to_move = go_to_this_cell(way['delete_move'])
            # add_way_to_door = {'x': js_obj['s']['x'], 'y': js_obj['s']['y'], 'p': to_move}
        else:
            # logger.info(f"buttons - '{buttons}' portal - '{portal}' key - '{key}'")
            to_move = REVERSE_WAYS[way['way']]
            # add_way_to_door = {'x': js_obj['s']['x'], 'y': js_obj['s']['y'], 'p': REVERSE_WAYS[way['way']]}
        # if map_to_door[add_way_to_door['x']][add_way_to_door['y']]:
        #     text_to_print = f"reverse way to door already exists '{map_to_door[add_way_to_door['x']][add_way_to_door['y']]}'"
        # else:
        #     text_to_print = f"add to map_to_door {add_way_to_door}"
        #     map_to_door[add_way_to_door['x']][add_way_to_door['y']] = add_way_to_door['p']
        map_to_door = add_way_door(map_to_door, my_coord, to_move)
        # logger.info(f"door found {text_to_print}")
        # logger.info("door found")
    return {'doors': doors, 'way': way, 'map_to_door': map_to_door}


def is_alive(js_obj) -> int:
    """
    Проверка жив = 1 или нет = 0
    """
    return js_obj['s']['alive']


def is_oil(js_obj) -> int:
    """
    Количество масла
    """
    return js_obj['s']['oil']


def is_floor(js_obj) -> int:
    """
    Текущий этаж
    """
    return js_obj['s']['floor']


def get_map(js_obj):
    js_obj['s']['map']
    logger.info(js_obj['s']['map'])
    # return js_obj['s']['map']


# @logger.catch()
def game(connect, html):
    """
    Ну типо тут запускаем пару прям команд пока
    """
    js_obj = get_satatus(connect, html)
    js_obj = is_attack(connect, js_obj)
    floor = is_floor(js_obj)
    logger.info(f"first floor - '{floor}'")

    # make_file(str(js_obj), "start_js_obj")
    # weapons = js_obj['s']['weapons']
    # # logger.error(f"weapons - '{weapons}'")
    # dict_weapons = {}
    # for key, value in weapons.items():
    #     dict_weapons[value['name']] = {"use": key, 'count': value['count']}
    # logger.error(f"dict_weapons - '{dict_weapons}'")

    while floor < int(config.FLOOR):
    # while floor < 8:
        map_to_go = create_map()
        map_to_port = create_map()
        map_to_door = create_map()
        portal = False
        doors = False
        buttons = False
        key = False
        go = True
        way = {}
        iter_number = 1
        logger.info(f"-----------iter number '{iter_number}'----------------")
        way['delete_move'] = ''
        way['way'] = ''
        while go:
            """-----KEY--------"""
            key = check_key(js_obj, key)
            """############ -----PORTAL--------##############"""
            data_portal = check_portal(js_obj, portal, map_to_port, way)
            portal = data_portal['portal']
            map_to_port = data_portal['map_to_port']
            """############ -----BUTTONS--------##############"""
            buttons = check_buttons(js_obj, buttons)
            """############ -----DOORS--------##############"""
            data_doors = check_doors(js_obj, doors, map_to_door, way, buttons, portal, key)
            way = data_doors['way']
            doors = data_doors['doors']
            map_to_door = data_doors['map_to_door']

            way = next_step(js_obj, map_to_go, way['delete_move'])
            """############ -----CHECK--------##############"""
            if (buttons and portal) and (doors and key):
                logger.info("STOP ITERATION!!!\n WE FIND EVERYTHING!!!")
                # logger.info(f"buttons - '{buttons}' portal - \
                #     '{portal}' doors - '{doors}' key - '{key}'")
                go = False
                js_obj = go_to_door(connect, js_obj, map_to_door, map_to_port)
                js_obj = go_to_port(connect, js_obj, map_to_port)
                js_obj = go_to_next_level(connect, js_obj)
            else:
                # logger.info(f"way {way} --------------------------------")
                js_obj = ways_to_go(connect, js_obj, way['way'])
                # way['old_way']
            # logger.debug(f" js_obj {js_obj}")
            if is_alive(js_obj) == 0:
                go = False
                logger.info("DEAD!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # print(f"IS OIL - '{is_oil(js_obj)}'")
            if is_oil(js_obj) == 0:
                go = False
                logger.info(f"STOP OIL OFF - '{is_oil(js_obj)}'")
            iter_number += 1
            logger.info(f"----------iter number '{iter_number}'-----------")

        floor = is_floor(js_obj)
        logger.info(f"floor - '{floor}'")
        if is_oil(js_obj) == 0:
            floor = 33
            logger.info(f"STOP OIL OFF - '{is_oil(js_obj)}'")
        if is_alive(js_obj) == 0:
            floor = 33
            logger.info(f"DEAD!!!!!!!!!!!!!!!!!!!!!!!!! floor - '{floor}'")
        # logger.info(f"map_to_port --------------- \n{map_to_port}")
        # logger.info(f"map_to_door --------------- \n{map_to_door}")
    return "All Done"
