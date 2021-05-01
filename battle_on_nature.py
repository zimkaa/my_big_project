from decimal import Decimal
import json
import pandas as pd
import requests

from loguru import logger

import config
from my_time import my_timer
from request_to_nl import get_html, post_html, get_data, log_in, set_session


def my_ip(proxies=None):
    """
    Get session IP
    """
    answer = requests.get(config.CHECKER_IP_SITE,
                          headers=config.HEADER, proxies=proxies)
    return answer.text


def parse_end_battle(soup):
    """
    Create query to end battle
    """
    fexp = soup[5].replace('var fexp = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(',')
    data = {
        "get_id": "61",
        "act": "7",
        "fexp": fexp[0],
        "fres": fexp[1],
        "vcode": fexp[3],
        "ftype": fexp[5],
        "min1": fexp[8],
        "max1": fexp[9],
        "min2": fexp[10],
        "max2": fexp[11],
        "sum1": fexp[12],
        "sum2": fexp[13]
    }
    return data


def use_mp(magic_in, alchemy, my_mp, ina, my_od, mp_need):
    """
    Create string to use mp
    """
    not_alchemy = ["277", "207", "242", "208", "205", "206", "269", "270", "320"]
    magic = []
    for obj in magic_in:
        if obj not in not_alchemy:
            magic.append(obj)
    if not magic:
        return {"ina": ina, "my_od": my_od}
    dict_name_boost_mp = {
        'name': [
            "Тыквенное зелье", "Превосходное Зелье Маны",
            "Зелье Восстановления Маны", "Восстановление MP"
        ],
        'code': [337, 521, 306, 33],
        'priority': [0, 1, 2, 3],
        'mp_boost': [999, 500, 100, 50],
        'od': [30, 30, 30, 30]
    }
    df = pd.DataFrame(dict_name_boost_mp)
    query = []
    list_element = []
    for num, element in enumerate(magic):
        element = int(element)
        for index in df.index:
            if df['code'][index] == element:
                query.append(f"{element}_{alchemy[num]}@")
                list_element.append(element)
    new_df = pd.DataFrame()
    for name in list_element:
        result = df[df['code'] == name]
        new_df = new_df.append(result, ignore_index=True)
    new_df['query'] = query
    sorted_list = new_df.sort_values(by='priority')
    if my_mp <= mp_need:
        boost_mp = 0
        query = ""
        for index in sorted_list.index:
            boost_mp += sorted_list['mp_boost'][index]
            query += sorted_list['query'][index]
            condition = boost_mp - mp_need
            logger.info(f"b my_od - {my_od}")
            my_od -= sorted_list['od'][index]
            logger.info(f"a my_od - {my_od}")
            if condition >= 0 and my_od <= 30:
                ina += query
                break
            else:
                ina += query
    return {"ina": ina, "my_od": my_od}


def get_query(list_hits, df):
    inu = ""
    for num, value in enumerate(list_hits):
        mp_cost = df[df['code'] == value].iloc[0]['mp_cost']
        inu += f"{num}_{value}_{mp_cost}@"
    return inu


def get_warrior_magic(magic_in, ina, my_od, fight_pm):
    """
    Логика смотри какой удар возможен и делает его
    """
    magic = {
        'name': [
            "Толчок", "Невероятная точность",
            "Второе дыхание", "Дубовая кожа",
            "Алмазная кожа"
        ],
        'code': [381, 479, 483, 478, 482],
        'od': [50, 100, 50, 50, 100]
    }
    magic_df = pd.DataFrame(magic)
    list_element = []
    for element in magic_in:
        element = int(element)
        for index in magic_df.index:
            if magic_df['code'][index] == element:
                list_element.append(element)
    fight_pm = int(fight_pm)
    for index in magic_df.index:
        od = int(magic_df['od'][index])
        if magic_df['code'][index] in list_element:
            if my_od >= (fight_pm + od):
                ina += f"{magic_df['code'][index]}@"
                my_od -= magic_df['od'][index]
                if my_od >= (fight_pm + 90) and magic_df['code'][index] == 478:
                    ina += "265@"
                    my_od -= 90
                break
    return {"my_od": my_od, "ina": ina}


def get_simple_warrior_hit(fight_pm, my_od, df):
    list_hits = []
    big = int(df['od'][0])
    small = int(df['od'][1])
    if my_od >= (big * 3 + 75):
        list_hits = [df['code'][0] for _ in range(3)]
        my_od -= big * 3 + 75
    elif my_od >= (big * 2 + 75 + small):
        list_hits = [df['code'][0] for _ in range(2)]
        list_hits.append(df['code'][1])
        my_od -= big * 2 + small + 75
    elif my_od >= (big + 75 + small * 2):
        list_hits = [df['code'][1] for _ in range(2)]
        list_hits.append(df['code'][0])
        my_od -= big + small * 2 + 75
    elif my_od >= (75 + small * 3):
        list_hits = [df['code'][1] for _ in range(3)]
        my_od -= small * 3 + 75
    elif my_od >= (big * 2 + 25):
        list_hits = [df['code'][0] for _ in range(2)]
        my_od -= big * 2 + 25
    elif my_od >= (big + small + 25):
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        my_od -= big + small + 25
    elif my_od >= (small * 2 + 25):
        list_hits = [df['code'][1] for _ in range(2)]
        my_od -= small * 2 + 25
    elif my_od >= big:
        list_hits.append(df['code'][0])
        my_od -= big
    elif my_od >= small:
        list_hits.append(df['code'][1])
        my_od -= small
    return {"my_od": my_od, "hits": list_hits}


def orc_25_hunter(lives_g1, magic_in, my_od, my_mp, alchemy, fight_pm):
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    need_mp = 100     # --------------------------------------------------------------------
    data_ues_mp = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = data_ues_mp['ina']
    my_od = data_ues_mp['my_od']
    simple = int(fight_pm)
    pinpoint = simple + 20
    data_magic = get_warrior_magic(magic_in, ina, my_od, simple)
    ina = data_magic['ina']
    my_od = data_magic['my_od']
    stable_warrior_hits = {
        'name': [
            "Прицельный", "Простой"
        ],
        'code': [1, 0],
        'mp_cost': [0, 0],
        'od': [pinpoint, simple]
    }
    stable_warrior_hits_df = pd.DataFrame(stable_warrior_hits)
    data_simple_hit = get_simple_warrior_hit(simple, my_od, stable_warrior_hits_df)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_warrior_hits_df)

    return {"inu": inu, "ina": ina, "inb": inb}


def loginc(data):
    param_ow = data['param_ow']
    param_en = data['param_en']
    fight_pm = data['fight_pm']
    fight_ty = data['fight_ty']
    lives_g1 = data['lives_g1']
    lives_g2 = data['lives_g2']
    magic_in = data['magic_in']
    alchemy = data['alchemy']
    # {param_en[0]}
    # name = param_en[0].encode('utf-8')
    name = ""
    text = f"name {name} bot level lives_g1 - '{param_en[5]}' HP - '{lives_g1[2]}' - \
        OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    logger.error(text)
    my_od = Decimal(fight_pm[1])
    small_heal = Decimal(param_ow[2]) * Decimal(0.45)
    big_heal = Decimal(param_ow[2]) * Decimal(0.4)
    need_heel = Decimal(param_ow[2]) * Decimal(0.2)
    my_mp = Decimal(param_ow[3])
    my_hp = Decimal(param_ow[1])
    if param_en[0] == "Огр-защитник":
        logger.debug("orc 25")
        data = orc_25_hunter(lives_g1, magic_in, my_od, my_mp, alchemy, fight_pm[2])
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    else:
        error = Exception("Нет ботов")
        raise error
    logger.debug(f"inu-{inu} inb-{inb} ina-{ina} my_od-{my_od} my_mp-{my_mp}")
    data = {
        "post_id": "7",
        "vcode": fight_pm[4],
        "enemy": fight_pm[5],
        "group": fight_pm[6],
        "inf_bot": fight_pm[7],
        "inf_zb": fight_pm[10],
        "lev_bot": param_en[5],
        "ftr": fight_ty[2],
        "inu": inu,
        "inb": inb,
        "ina": ina
    }
    return data


def parse_fight(soup):
    """
    Get data and start logic
    """
    elementos = soup.find(language="JavaScript")
    text = str(elementos).split('\n')
    if len(text) == 9:
        data = parse_end_battle(text)
        return data
    fight_ty = text[1].replace('var fight_ty = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(",")
    param_ow = text[2].replace('var param_ow = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(",")
    param_en = text[9].replace('var param_en = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(",")
    fight_pm = text[12].replace('var fight_pm = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(",")
    lives_g1 = text[4].replace('var lives_g1 = ', '').replace(';', '')\
        .replace('"', '').replace('[', '').replace(']', '').split(",")
    lives_g2 = text[5].replace('var lives_g2 = ', '').replace(';', '')\
        .replace('"', '').replace('[', '').replace(']', '').split(",")
    alchemy = text[6].replace('var alchemy = ', '')\
        .replace('[', '').replace('];', '').split(",")
    magic_in = text[8].replace('var magic_in = ', '').replace(';', '')\
        .replace('[', '').replace(']', '').split(",")
    data_to_fight = {
        "fight_ty": fight_ty,
        "param_ow": param_ow,
        "param_en": param_en,
        "fight_pm": fight_pm,
        "lives_g1": lives_g1,
        "lives_g2": lives_g2,
        "magic_in": magic_in,
        "alchemy": alchemy
    }
    data = loginc(data_to_fight)
    return data


def fighting(connect, html, fight=True):
    """
    Start fight
    """
    if fight:
        number_iteration = 0
        while fight:
            data = stop_or_hit(connect, html)
            html = data['html']
            fight = data['stop']
            number_iteration += 1
    else:
        number_iteration = 0
        while number_iteration < 1:
            data = stop_or_hit(connect, html)
            html = data['html']
            fight = data['stop']
            if not fight:
                number_iteration = 100
            number_iteration += 1
    return html


def stop_or_hit(connect, html):
    """
    Check battle for the stop or hit
    """
    soup = get_data(html)
    data = parse_fight(soup)
    url = config.URL_MAIN
    if "post_id" in data.keys():
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        stop = True
    else:
        logger.info("get a request for the end battle")
        html = get_html(connect, url, config.HEADER, config.PROXYES, data)
        stop = False
    return {"html": html, "stop": stop}


def main():
    ip = my_ip(config.PROXYES)
    logger.info(f"-------ip------- {ip}")
    if config.PROXY_IP in ip:
        logger.info("ip IS proxy YES")
        connect = set_session()
        html = log_in(connect)
        # fighting(connect, html, False)
        fighting(connect, html)


if __name__ == '__main__':
    logger.add("fight_nature.log", format="{time} {level} {message}", level="DEBUG",
               rotation="24 hour", compression="zip")
    main()
