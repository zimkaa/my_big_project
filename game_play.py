from decimal import Decimal
import json
import re
# import requests
from time import sleep
from typing import Union

from loguru import logger

import config
# from fight_dangeon_24 import fighting
# from fight_dangeon_23_warrior import fighting
from mag_fight_dangeon_24 import fighting
from request_to_nl import get_html, get_data, post_html
from implementation import (
    up, right, down, create_right_way, left, find_way_to,
    find_near_way, uncharted_path,
)


CHANGE_NAME = {
    "moveDown": "openDown",
    "moveLeft": "openLeft",
    "moveUp": "openUp",
    "moveRight": "openRight",
}


SHORT_NAME = {
    "moveDown": "d",
    "moveLeft": "l",
    "moveUp": "u",
    "moveRight": "r",
}


def string_info(js_obj: object) -> str:
    """
    Create string to debug log
    """
    coord_x = js_obj['s']['x']
    coord_y = js_obj['s']['y']
    way_to_go = js_obj['s']['map'][js_obj['s']['x']][js_obj['s']['y']].get('p')
    oil = is_oil(js_obj)
    oil_price = js_obj['s']['oilPrice']
    floor = is_floor(js_obj)
    if js_obj['s']['own']:
        key = True
    else:
        key = False
    buttons = js_obj['s'].get('buttonsLeft')
    doors = False
    text = f"oil- '{oil}' oilPrice- '{oil_price}' floor- '{floor}'"
    text += f" coord= '{coord_x}{coord_y}' '{way_to_go}'"
    text += f" key= '{key}' buttons= '{buttons}'"
    for num_x, row in enumerate(js_obj['s']['map']):
        for num_y, _ in enumerate(row):
            exist = js_obj['s']['map'][num_x][num_y]
            if exist:
                if exist.get('doors'):
                    doors = True
    text += f" doors= '{doors}'"
    return text


def restoring_mana_and_hp(connect: object, html: object,
                          healing: float) -> object:
    """
    Chek HP/MP and restore
    """
    soup = get_data(html)
    elementos = soup.find(language="JavaScript")
    text = str(elementos).split('\n')
    inshp = text[2].replace('var inshp = ', '').replace('];', '')\
        .replace('[', '').split(",")
    my_max_hp = Decimal(inshp[1])
    my_max_mp = Decimal(inshp[3])
    my_hp = Decimal(inshp[0])
    my_mp = Decimal(inshp[2])
    min_hp = my_max_hp * Decimal(healing)
    min_mp = my_max_mp * Decimal(healing)
    count_hp = 0
    count_mp = 0
    if my_hp <= min_hp:
        # count_hp = Decimal((min_hp - my_hp) / 100).quantize(Decimal('1'))
        count_hp = Decimal((min_hp - my_hp) / 500).quantize(Decimal('1'))
    if my_mp <= min_mp:
        # count_mp = Decimal((min_mp - my_mp) / 100).quantize(Decimal('1'))
        count_mp = Decimal((min_mp - my_mp) / 500).quantize(Decimal('1'))
    if count_hp >= count_mp:
        count = count_hp
    else:
        count = count_mp
    if count:
        logger.error(f"count {count}")
        js_obj = get_satatus(connect, html)
        for _ in range(int(count)):
            key = "useWeapon.w27_521"  # BIG MP!!!
            # key = "useWeapon.w27_309"  # 309 --- Зелье Энергии
            js_obj['a'][key]
            item = key.replace('useWeapon.', '')
            vcode = js_obj['a'].get(key)
            data = {
                "type": "dungeon",
                "action": "useWeapon",
                "item": item,
                "vcode": vcode,
            }
            try:
                html = post_html(connect, config.URL_EVENT, config.HEADER,
                                 config.PROXYES, data)
            except Exception:
                # requests.get("https://armorwp.com/custom.php?text=NO_POTION_MP_TURN")
                error = Exception("----NO POTION MP!!!---")
                raise error
            if key == "useWeapon.w27_521":
                logger.error(f"use weapon {key} 521: BIG MP!!!")
            else:
                logger.error(f"use weapon {key} 309: potion energy!!!")
            js_obj = json.loads(html.text)
    else:
        logger.error(f"Not use HP/MP count {count}")
        js_obj = get_satatus(connect, html)
    return js_obj


def is_attack(connect: object, js_obj: object) -> object:
    """
    Сheck the presence of an enemy and attack
    Take items
    """
    # logger.error(f"js_obj {js_obj}")
    if js_obj['a'].get('attack'):
        vcode = js_obj['a'].get('attack')
        url = config.URL_EVENT
        data = {
            "type": "dungeon",
            "action": "attack",
            "vcode": vcode,
        }
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        html = get_html(connect, config.URL_MAIN,
                        config.HEADER, config.PROXYES)
        html = fighting(connect, html)

        js_obj = get_satatus(connect, html)
        js_obj = check_pickup(connect, js_obj)
        js_obj = check_pickup(connect, js_obj)
    else:
        js_obj = check_pickup(connect, js_obj)
        js_obj = check_pickup(connect, js_obj)
    return js_obj


def go_to_next_level(connect: object, js_obj: object) -> object:
    """
    Go to next level
    """
    if js_obj['a'].get('moveDeep'):
        vcode = js_obj['a'].get('moveDeep')
        url = config.URL_EVENT
        data = {
            "type": "dungeon",
            "action": "moveDeep",
            "vcode": vcode,
        }
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        logger.info("--------NEXT LEVEL---------")
        return json.loads(html.text)
    else:
        logger.debug(f"-------can't activate portal-------\n{js_obj}")
        return js_obj


def check_pickup(connect: object, js_obj: object) -> object:
    """
    Take items
    """
    for key in js_obj['a'].keys():
        if key.find("pickup") != -1:
            item = key.replace('pickup.', '')
            vcode = js_obj['a'].get(key)
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


def parse_dungeon(soup_object) -> dict:
    """
    Prepare 'data' for request
    """
    elementos = soup_object.find(language="JavaScript")
    text = str(elementos).split('\n')
    # logger.info(f"{soup_object}")
    var_obj_actions = text[9].replace('var objActions = ', '').replace(';', '')
    actions = json.loads(var_obj_actions)
    data = {
        "type": "dungeon",
        "action": "getStatus",
        "vcode": actions.get('getStatus'),
    }
    return data


def get_satatus(connect: object, html: object) -> object:
    """
    Get status. Need to take json answer
    """
    soup = get_data(html)
    status_url = config.URL_EVENT
    data = parse_dungeon(soup)
    html = post_html(connect, status_url, config.HEADER, config.PROXYES, data)
    return json.loads(html.text)


# def create_map() -> list:
#     """
#     Создаем пустые карты
#     """
#     map_to = [
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#         ["", "", "", "", "", "", ""],
#     ]
#     return map_to


def check_key(js_obj: object, key: bool) -> bool:
    """
    Checks if the key is found?
    """
    if not key:
        if js_obj['s']['own']:
            key = True
    return key


def check_buttons(js_obj: object, buttons: bool) -> bool:
    """
    Checks if the buttons is found?
    """
    if not buttons:
        number = js_obj['s'].get('buttonsLeft')
        if number == 0:
            buttons = True
    return buttons


def is_alive(js_obj: object) -> int:
    """
    Alive=1  Dead=0
    """
    return js_obj['s']['alive']


def is_oil(js_obj: object) -> int:
    """
    Count oil
    """
    return js_obj['s']['oil']


def is_floor(js_obj: object) -> int:
    """
    Number floor
    """
    return js_obj['s']['floor']


def check_reward(js_obj: object, reward: bool) -> bool:
    """
    Checks if the reward geted?
    """
    if not reward:
        for num_x, coord_x in enumerate(js_obj['s']['map']):
            for num_y, _ in enumerate(coord_x):
                cell_exist = js_obj['s']['map'][num_x][num_y]
                if cell_exist:
                    if cell_exist.get('doors'):
                        [coord] = cell_exist.get('doors').keys()
                        neighbors = {
                            "u": up,
                            "r": right,
                            "d": down,
                            "l": left,
                        }
                        coord_reward = f"{neighbors[coord](num_x, num_y)}"
                        rew_x = int(coord_reward[0])
                        rew_y = int(coord_reward[1])
                        reward_exist = js_obj['s']['map'][rew_x][rew_y]
                        if reward_exist:
                            reward = True
    return reward


def check_doors(js_obj: object, doors: bool) -> dict:
    """
    Checks if the doors is found?
    """
    if not doors:
        for num_x, coord_x in enumerate(js_obj['s']['map']):
            for num_y, _ in enumerate(coord_x):
                exist = js_obj['s']['map'][num_x][num_y]
                if exist:
                    if exist.get('doors'):
                        doors = True
                        [coord] = exist.get('doors').keys()
                        neighbors = {
                            "u": up,
                            "r": right,
                            "d": down,
                            "l": left,
                        }
                        coord_doors = f"{neighbors[coord](num_x, num_y)}"
                        return {"doors": doors, "coord_doors": coord_doors}
    return {"doors": doors}


def check_portal(js_obj: object, portal: bool) -> bool:
    """
    Checks if the portal is found?
    """
    if not portal:
        for num_x, coord_x in enumerate(js_obj['s']['map']):
            for num_y, _ in enumerate(coord_x):
                exist = js_obj['s']['map'][num_x][num_y]
                if exist:
                    if exist.get('v') == 11:
                        portal = True
                        return portal
    return portal


def going(connect: object, js_obj: object, way: str, iter_number: int) -> dict:
    """
    Make reqest to go
    :param: way [str] like 'moveDown'
    """
    url = config.URL + "/ch.php?0.3296457688728473&show=1&fyo=0"
    get_html(connect, url)
    html = get_html(connect, config.URL_MAIN)
    js_obj = get_satatus(connect, html)
    oil = is_oil(js_obj)
    alive = is_alive(js_obj)
    if alive == 0 or oil == 0:
        # requests.get("https://armorwp.com/message.php")
        error = Exception(f"Can't move oil - {oil} alive - {alive}")
        raise error
    if js_obj['a'].get(way):
        vcode = js_obj['a'].get(way)
        first_part = r"^[a-z]+[^A-Z]"
        [action] = re.findall(first_part, way)
        second_part = r"[A-Z][a-z]+"
        [direction] = re.findall(second_part, way)
        data = {
            "type": "dungeon",
            "action": action,
            "direction": direction.lower(),
            "vcode": vcode,
        }
        html = post_html(connect, config.URL_EVENT, data=data)
        sleep(5.5)
        js_obj = check_pickup(connect, json.loads(html.text))
        if js_obj['a'].get('attack'):
            """
            Поднимаем ХП
            """
            html = get_html(connect, config.URL_MAIN,
                            config.HEADER, config.PROXYES)
            healing = 0.9
            js_obj = restoring_mana_and_hp(connect, html, healing)
            js_obj = is_attack(connect, js_obj)
    else:
        key = check_key(js_obj, False)
        if key:
            logger.info("GO TO DOOR IN GOING\n'GO TO DOOR IN GOING'")
            action = "open"
            part = r"[A-Z][a-z]+"
            [direction] = re.findall(part, way)
            new_way = action + direction
            vcode = js_obj['a'].get(new_way)
            data = {
                "type": "dungeon",
                "action": action,
                "direction": direction.lower(),
                "vcode": vcode,
            }
            html = post_html(connect, config.URL_EVENT, data=data)
            js_obj = json.loads(html.text)
            vcode = js_obj['a'].get(way)
            first_part = r"^[a-z]+[^A-Z]"
            [action] = re.findall(first_part, way)
            second_part = r"[A-Z][a-z]+"
            [direction] = re.findall(second_part, way)
            data = {
                "type": "dungeon",
                "action": action,
                "direction": direction.lower(),
                "vcode": vcode,
            }
            html = post_html(connect, config.URL_EVENT, data=data)
            sleep(5.5)
            js_obj = check_pickup(connect, json.loads(html.text))
            if js_obj['a'].get('attack'):
                """
                Поднимаем ХП
                """
                html = get_html(connect, config.URL_MAIN,
                                config.HEADER, config.PROXYES)
                # requests.get("https://armorwp.com/custom.php?text=BOSS_TURN")
                # error = Exception("----BOSSSSS----")
                # raise error
                healing = 0.99
                js_obj = restoring_mana_and_hp(connect, html, healing)
                js_obj = is_attack(connect, js_obj)
                boss = True
                logger.info(f"boss {boss}")
        else:
            logger.info(f"---- Trouble - NO KEY---'{way.upper()}' --------")
            text = string_info(js_obj)
            logger.info(text)
            # requests.get("https://armorwp.com/custom.php?text=UNKNOWN_TROUBLE")
            error = Exception(f"STOP ITER Trouble NO KEY BUT DOOR----'{way}'")
            raise error
    return {"js_obj": js_obj, "iter_number": iter_number}


def test_while(connect: object, js_obj: object,
               ways: list, iter_number: int) -> dict:
    """
    While for ways
    """
    for way in ways:
        data = going(connect, js_obj, way, iter_number)
        js_obj = data['js_obj']
        iter_number = data['iter_number']
        text = string_info(js_obj)
        logger.info(text)
        iter_number += 1
        logger.info(f"--iter number '{iter_number}'--- way '{way.upper()}'---")
    return {"js_obj": js_obj, "iter_number": iter_number}


def new_go(data: object) -> list:
    """
    Make first steps
    """
    not_visited = uncharted_path(data)
    logger.info(f"----------- not_visited '{not_visited}'----------------")
    if not_visited:
        go_to = find_near_way(data, not_visited)
        logger.info(f"----------- go_to '{go_to}'---- type '{type(go_to)}'")
        ways = create_right_way(data, go_to)
    else:
        ways = []
    return ways


def start_level() -> bool:
    """
    Initialize variables
    """
    return False, False, False, False, False


def going_to(connect: object, js_obj: object, coord: Union[str, list[str]],
             iter_number: int) -> dict:
    """
    Go to coord
    """
    way_to = create_right_way(js_obj, coord)
    data = test_while(connect, js_obj, way_to, iter_number)
    js_obj = data['js_obj']
    iter_number = data['iter_number']
    return {"js_obj": js_obj, "iter_number": iter_number}


def going_to_reward(connect: object, js_obj: object, coord: list,
                    iter_number: int) -> dict:
    """
    Go to reward
    :param: coord - list like ["12"]
    """
    data = test_while(connect, js_obj, coord, iter_number)
    js_obj = data['js_obj']
    iter_number = data['iter_number']
    return {"js_obj": js_obj, "iter_number": iter_number}


def get_coord_portal(js_obj: object) -> str:
    """
    Finde coord portal
    """
    for num_x, coord_x in enumerate(js_obj['s']['map']):
        for num_y, _ in enumerate(coord_x):
            exest = js_obj['s']['map'][num_x][num_y]
            if exest:
                port = js_obj['s']['map'][num_x][num_y].get('v')
                if port == 11:
                    coord = f"{num_x}{num_y}"
                    logger.info(f"coord '{coord}'")
    return coord


def game(connect: object, html: object) -> str:
    js_obj = get_satatus(connect, html)
    js_obj = is_attack(connect, js_obj)
    floor = is_floor(js_obj)
    logger.info(f"start floor - '{floor}'")
    # weapons = js_obj['s']['weapons']
    # logger.error(f"weapons - '{weapons}'")
    # dict_weapons = {}
    # for key, value in weapons.items():
    #     dict_weapons[value['name']] = {"use": key, 'count': value['count']}
    # logger.error(f"dict_weapons - '{dict_weapons}'")
    """
    Эликсир Быстроты - w61_106
    Слеза Создателя - w28_77
    Свиток каменной кожи - w28_20
    Превосходное Зелье Ореола - w27_515
    Превосходное Зелье Человек-Гора - w27_518
    Превосходное Зелье Панциря - w27_517
    Свиток Магии Воздуха - w28_92
    Свиток Величия - w28_21
    Зелье Кровожадности - w61_105
    Молодильное яблочко - w61_110
    Искрящийся мандарин - w61_162
    """
    # dict_weap = {
    #     "2": [2, "28_21"],
    #     "4": [2, "28_21"],
    #     "6": [2, "28_21"],
    # }
    while floor < int(config.FLOOR):
        portal, doors, buttons, key, reward = start_level()
        iter_number = 0
        logger.info(f"-----------iter number '{iter_number}'----------------")
        text = string_info(js_obj)
        logger.info(text)
        while True:
            key = check_key(js_obj, key)

            data_doors = check_doors(js_obj, doors)
            doors = data_doors['doors']
            if data_doors.get('coord_doors'):
                coord_doors = data_doors['coord_doors']

            reward = check_reward(js_obj, reward)
            logger.info(f"reward - {reward}")

            if not reward:
                if doors and key:
                    logger.info("KEY AND DOOR FIND GO TO REWARD!!!!!!!!!!!")
                    way_to = find_way_to(js_obj, coord_doors)
                    ways_to_door = create_right_way(js_obj, way_to)
                    if len(ways_to_door) < 5:
                        logger.info("neeed to go to door")
                        # error = Exception(f"neeed to go to door {start}")
                        # raise error
                        data = going_to_reward(
                            connect, js_obj, ways_to_door, iter_number,
                        )
                        js_obj = data['js_obj']
                        iter_number = data['iter_number']
                    else:
                        first_part = f"WAY TO DOOR TO LONG- {ways_to_door}"
                        second_part = f" type {type(ways_to_door)}"
                        text = first_part + second_part
                        logger.info(text)

            buttons = check_buttons(js_obj, buttons)

            portal = check_portal(js_obj, portal)
            logger.info(f"portal - {portal}")

            if (buttons and portal) and (doors and key):
                if not reward:
                    way_to = find_way_to(js_obj, coord_doors)
                    ways_to_door = create_right_way(js_obj, way_to)
                    logger.info("ALL DONE GO TO DOOR")
                    data = going_to_reward(
                        connect, js_obj, ways_to_door, iter_number,
                    )
                    js_obj = data['js_obj']
                    iter_number = data['iter_number']
                coord_port = get_coord_portal(js_obj)
                my_coord = f"{js_obj['s']['x']}{js_obj['s']['y']}"
                if coord_port == my_coord:
                    logger.info("UP NEXT LEVEL")
                    js_obj = go_to_next_level(connect, js_obj)
                else:
                    go_to_port = find_way_to(js_obj, coord_port)
                    data = going_to(connect, js_obj, go_to_port, iter_number)
                    js_obj = data['js_obj']
                    iter_number = data['iter_number']
                    logger.info("UP NEXT LEVEL")
                    js_obj = go_to_next_level(connect, js_obj)
                break

            ways = new_go(js_obj)
            if ways:
                data = test_while(connect, js_obj, ways, iter_number)
                js_obj = data['js_obj']
                iter_number = data['iter_number']

        floor = is_floor(js_obj)
        logger.info(f"\nfloor - '{floor}'")
    return "All Done"
