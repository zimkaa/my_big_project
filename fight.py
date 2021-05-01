from decimal import Decimal
import json
import pandas as pd
import requests

from loguru import logger

import config
from my_time import my_timer
from request_to_nl import get_html, post_html, get_data, log_in, set_session


logger.add("fight.log", format="{time} {level} {message}", level="DEBUG",
           rotation="24 hour", compression="zip")


def my_ip(proxies=None):
    """
    Получаем текущий IP сессии
    """
    answer = requests.get(config.CHECKER_IP_SITE,
                          headers=config.HEADER, proxies=proxies)
    return answer.text


# @my_timer("parse_end_battle")
def parse_end_battle(soup):
    """
    Составляем запрос на выход из боя
    """
    fexp = soup[5].replace('var fexp = ', '').replace('];', '')\
        .replace('"', '').replace('[', '').split(',')
    # logger.info(f"------fexp-------\n{fexp}")
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
    # logger.info(f"-------end fight-------")
    return data


def use_mp(magic_in, alchemy, my_mp, ina, my_od, mp_need):
    """
    Логика смотрит что выпить с пояса при определенном количестве маны пока жестко меньше 1к
    """
    not_alchemy = ["277", "207", "242", "208", "205", "206", "269", "270", "320"]
    magic = []
    for obj in magic_in:
        # logger.info(f"obj {obj} type(obj) {type(obj)}")
        if obj not in not_alchemy:
            magic.append(obj)
    # logger.info(f"magic {magic} my_od - {my_od}")
    if not magic:
        # logger.info(f"not magic - {my_od}")
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
        # logger.info(f"num {num} element {element}")
        element = int(element)
        # logger.info(f"type {type(element)}")
        for index in df.index:
            if df['code'][index] == element:
                query.append(f"{element}_{alchemy[num]}@")
                list_element.append(element)
    # logger.info(list_element)
    new_df = pd.DataFrame()
    for name in list_element:
        result = df[df['code'] == name]
        new_df = new_df.append(result, ignore_index=True)
    new_df['query'] = query
    sorted_list = new_df.sort_values(by='priority')
    # my_mp = 999
    # mp_need = 1000
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
    # logger.debug(f"out of use_mp  ina - {ina} my_od - {my_od} ")
    return {"ina": ina, "my_od": my_od}


# def check_item(magic_in, alchemy, mp, ina, my_od, hit_dict2=None):
#     """
#     Логика смотрит что выпить с пояса
#     """
#     not_alchemy = ["277", "207", "242", "208", "205", "206", "269", "270", "320"]
#     magic = []
#     for obj in magic_in:
#         # logger.info(f"obj {obj} type(obj) {type(obj)}")
#         if obj not in not_alchemy:
#             magic.append(obj)
#     logger.info(f"magic {magic}")
#     if not magic:
#         return {"ina": ina, "my_od": my_od}
#     # heal_mp = ["Превосходное Зелье Маны", "Зелье Восстановления Маны", "Восстановление MP", "Тыквенное зелье"]
#     heal_mp = ["521", "306", "33", "337"]
#     count_element = {}
#     to_heal = []
#     for num, element in enumerate(magic_in[:3]):
#         if element in heal_mp:
#             magic_in[:3].count(element)
#             to_heal.append(f"{element}_{alchemy[num]}@")
#             if count_element.get(element):
#                 count_element[element] += 1
#             else:
#                 count_element[element] = {'count': 1, "number": number}
#     logger.info(f"count_element {count_element}")

#     if my_mp >= 1000:
#         if count_element["521"] == 1:

#     elif my_mp >= 500:
#         pass


#     for num, name in enumerate(obj_check):
#         if name in heal_mp:
#             # my_od -= hit_dict2[name]['od']
#             # ina += f"{hit_dict2[name]['number']}_{alchemy[num]}@"
#             my_od -= 30
#             ina += f"{name}_{alchemy[num]}@"
#             logger.info(f"name in heal_mp {name}")
#     logger.info(f"ina {ina} my_od {my_od} ")
#     return {"ina": ina, "my_od": my_od}


def check_hit(data, my_od, new_df, list_hits):
    """
    Проверяет на возможность сделать удар
    """
    logger.error(f"start check_hit my_od - {my_od}")
    logger.error(f"data['count_hit'] - {data['count_hit']}")
    for _ in range(data['count_hit']):
        list_hits.append(new_df['code'][2])
        my_od -= new_df['od'][2]
    my_od -= data['use_od']
    # logger.error(f"end chek hit my_od - {my_od} hits - {list_hits}")
    return {"my_od": my_od, "hits": list_hits}


def get_hit(magic_in, inu, my_od):
    """
    Логика смотри какой удар возможен и делает его
    """
    # logger.debug(f"start get_hit inu - {inu}")
    hits = {
        'name': [
            "Гнев Титанов",
            "Ураган", "Молния",
        ],
        'code': [207, 208, 205],
        'mp_cost': [75, 100, 50],
        'od': [100, 100, 100]
    }
    hits_df = pd.DataFrame(hits)
    list_element = []
    for element in magic_in:
        element = int(element)
        for index in hits_df.index:
            if hits_df['code'][index] == element:
                list_element.append(element)
    stable_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [5, 5],
        'od': [90, 50]
    }
    stable_hits_df = pd.DataFrame(stable_hits)
    # logger.debug(f"list_element - {list_element}")
    for name in list_element:
        result = hits_df[hits_df['code'] == name]
        stable_hits_df = stable_hits_df.append(result, ignore_index=True)
    list_hits = []
    # logger.debug(f"start get_hit list_element - {list_element}")
    for index in stable_hits_df.index[2:]:
        # logger.error(f"hit code - {stable_hits_df['code'][index]}")
        # logger.error(f"my_od - {my_od}")
        if my_od >= 375:
            logger.error("my_od >= 375")
            count = 3
            use_od = 25 * count
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        elif my_od >= 225:
            # logger.error("my_od >= 225")
            count = 2
            use_od = 25 * (count - 1)
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        elif my_od >= 100:
            # logger.error("my_od >= 100")
            count = 1
            use_od = 25 * (count - 1)
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        else:
            data = {"count_hit": 0}
            logger.error("break")
            break
    else:
        data = {"count_hit": 0}
        # logger.error("for else")
    # logger.error(f"list_hits {list_hits}")
    # logger.error(f"my_od {my_od}")
    # logger.error(f"data {data}")
    data_simple_hit = get_simple_mag_hit(data, stable_hits_df, my_od, list_hits)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_hits_df)
    # logger.info(f"inu {inu} my_od {my_od} ")
    return {"inu": inu, "my_od": my_od}


def get_query(list_hits, df):
    inu = ""
    for num, value in enumerate(list_hits):
        mp_cost = df[df['code'] == value].iloc[0]['mp_cost']
        inu += f"{num}_{value}_{mp_cost}@"
    return inu


def get_simple_mag_hit(data, df, my_od, list_hits):
    if my_od >= 145 and data['count_hit'] == 2:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] + data['count_hit'] * 25
    elif my_od >= 100 and data['count_hit'] == 2:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + data['count_hit'] * 25
    if my_od >= 115 and data['count_hit'] == 1:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] + data['count_hit'] * 25
    elif my_od >= 75 and data['count_hit'] == 1:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + data['count_hit'] * 25
    if my_od >= 345 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] * 3 + 75
    elif my_od >= 305 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        my_od -= df['od'][0] * 2 + df['od'][1] + 75
    elif my_od >= 265 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][0] + df['od'][1] * 2 + 75
    elif my_od >= 225 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] * 3 + 75
    elif my_od >= 205 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] * 2 + 25
    elif my_od >= 165 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + df['od'][0] + 25
    elif my_od >= 125 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] * 2 + 25
    elif my_od >= 90 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0]
    elif my_od >= 50 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1]
    return {"my_od": my_od, "hits": list_hits}


def get_simple_warrior_hit(data, df, my_od, list_hits):
    if my_od >= 145 and data['count_hit'] == 2:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] + data['count_hit'] * 25
    elif my_od >= 100 and data['count_hit'] == 2:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + data['count_hit'] * 25
    if my_od >= 115 and data['count_hit'] == 1:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] + data['count_hit'] * 25
    elif my_od >= 75 and data['count_hit'] == 1:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + data['count_hit'] * 25
    if my_od >= 345 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] * 3 + 75
    elif my_od >= 305 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        my_od -= df['od'][0] * 2 + df['od'][1] + 75
    elif my_od >= 265 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][0] + df['od'][1] * 2 + 75
    elif my_od >= 225 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] * 3 + 75
    elif my_od >= 205 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][0])
        my_od -= df['od'][0] * 2 + 25
    elif my_od >= 165 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] + df['od'][0] + 25
    elif my_od >= 125 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        list_hits.append(df['code'][1])
        my_od -= df['od'][1] * 2 + 25
    elif my_od >= 90 and data['count_hit'] == 0:
        list_hits.append(df['code'][0])
        my_od -= df['od'][0]
    elif my_od >= 50 and data['count_hit'] == 0:
        list_hits.append(df['code'][1])
        my_od -= df['od'][1]
    return {"my_od": my_od, "hits": list_hits}


def get_warrior_magic(magic_in, ina, my_od, fight_pm):
    """
    Логика смотри какой удар возможен и делает его
    """
    # logger.debug(f"start get_hit inu - {inu}")
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
    # logger.debug(f"list_element - {list_element}")
    ina = ""
    for index in magic_df.index:
        # logger.error(f"hit code - {stable_hits_df['code'][index]}")
        # logger.error(f"my_od - {my_od}")
        if my_od >= (fight_pm + magic_df['od'][index]):
            logger.error(f"my_od >= (fight_pm + magic_df['od'][index]) - '{(fight_pm + magic_df['od'][index])}'")
            ina += f"{magic_df['code'][index]}@"
            my_od -= magic_df['od'][index]
            if my_od >= (fight_pm + 90) and magic_df['code'][index] == 478:
                ina += "265@"
                my_od -= 90
            break
    # logger.error(f"list_hits {list_hits}")
    # logger.error(f"my_od {my_od}")
    # logger.error(f"data {data}")

    # logger.info(f"inu {inu} my_od {my_od} ")
    return {"my_od": my_od, "ina": ina}


def get_simple_warrior_hit2(fight_pm, my_od, df):
    list_hits = []
    big = df['od'][0]
    small = df['od'][1]
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
    logger.error(f"hp_bots - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    need_mp = 1000     # --------------------------------------------------------------------
    data_ues_mp = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = data_ues_mp['ina']
    my_od = data_ues_mp['my_od']
    # need_od = 90 + fight_pm
    # if my_od >= need_od:
    #     if "265" in magic_in:
    #         ina += "265@"
    #         logger.error("magic vimpir")
    #         my_od -= 90

    data_magic = get_warrior_magic(magic_in, ina, my_od, fight_pm)
    ina = data_magic['ina']
    my_od = data_magic['my_od']

    stable_warrior_hits = {
        'name': [
            "Прицельный", "Простой"
        ],
        'code': [1, 0],
        'mp_cost': [0, 0],
        'od': [fight_pm + 20, fight_pm]
    }
    stable_warrior_hits_df = pd.DataFrame(stable_warrior_hits)
    data_simple_hit = get_simple_warrior_hit2(fight_pm, my_od, stable_warrior_hits_df)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_warrior_hits_df)




    # data = get_hit(magic_in, inu, my_od)
    # inu = data['inu']
    # my_od = data['my_od']
    return {"inu": inu, "ina": ina, "inb": inb}


def orc_24(lives_g1, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g1) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g1[number_iter])
        number_iter += 5
    # for hp_bot in hp_bots:
    #     if int(hp_bot) < 800:
    #         logger.error("bot HP < 800")
    #         if "206" in magic_in:
    #             magic_in.remove("206")
    #         if "269" in magic_in:
    #             magic_in.remove("269")
    logger.error(f"hp_bots - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    need_mp = 1000
    # logger.debug(f"before use_mp my_od - {my_od}")
    use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = use_mp_data['ina']
    my_od = use_mp_data['my_od']
    # logger.debug(f"after use_mp my_od - {use_mp_data['my_od']}")
    # logger.debug(f"my_od - {my_od}")
    if my_od >= 170:
        if "242" in magic_in:
            ina += "242@"
            # logger.error("magic 242@")
            my_od -= 100
    # logger.debug(f"before get hit my_od - {my_od}")
    get_hit_data = get_hit(magic_in, inu, my_od)
    inu = get_hit_data['inu']
    my_od = get_hit_data['my_od']
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    else:
        logger.error(f"hp_bots - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    need_mp = 1000
    # logger.debug(f"before use_mp my_od - {my_od}")
    use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = use_mp_data['ina']
    my_od = use_mp_data['my_od']
    # logger.debug(f"after use_mp my_od - {use_mp_data['my_od']}")
    # logger.debug(f"my_od - {my_od}")
    # if my_od >= 170:
    #     if "242" in magic_in:
    #         ina += "242@"
    #         # logger.error("magic 242@")
    #         my_od -= 100
    # logger.debug(f"before get hit my_od - {my_od}")
    get_hit_data = get_hit(magic_in, inu, my_od)
    inu = get_hit_data['inu']
    my_od = get_hit_data['my_od']
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_lich_warrior(lives_g2, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    if my_mp <= 900:
        logger.info(" my_mp < 500")
        ina = f"521_{alchemy[0]}@521_{alchemy[1]}@521_{alchemy[2]}@"
        my_od -= 90


    data_magic = get_warrior_magic(magic_in, ina, my_od, fight_pm)
    ina = data_magic['ina']
    my_od = data_magic['my_od']

    stable_warrior_hits = {
        'name': [
            "Прицельный", "Простой"
        ],
        'code': [1, 0],
        'mp_cost': [0, 0],
        'od': [fight_pm + 20, fight_pm]
    }
    df = pd.DataFrame(stable_warrior_hits)
    data_simple_hit = get_simple_warrior_hit2(fight_pm, my_od, stable_warrior_hits)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_warrior_hits)


    if my_od >= 375:
        if "207" in magic_in:
            inu += "0_207_75@1_207_75@2_207_75@"
            logger.error("anger")
            my_od -= 375
        elif "208" in magic_in:
            inu += "0_208_100@1_208_100@2_208_100@"
            logger.error("storm")
            my_od -= 375
        elif "205" in magic_in:
            inu += "0_205_50@1_205_50@2_205_50@"
            logger.error("lightning")
            my_od -= 375
        elif "206" in magic_in:
            inu += "0_206_150@1_206_150@"
            logger.error("chain lightning")
            my_od -= 275
        else:
            inu	+= "0_3_5@1_3_5@2_3_5@"
            logger.error("dable spirit")
            my_od -= 345
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_lich(lives_g2, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    if my_mp < 500:
        logger.info(" my_mp < 500")
        ina = f"521_{alchemy[0]}@521_{alchemy[1]}@521_{alchemy[2]}@"
        my_od -= 90
    if my_od >= 375:
        if "207" in magic_in:
            inu += "0_207_75@1_207_75@2_207_75@"
            logger.error("anger")
            my_od -= 375
        elif "208" in magic_in:
            inu += "0_208_100@1_208_100@2_208_100@"
            logger.error("storm")
            my_od -= 375
        elif "205" in magic_in:
            inu += "0_205_50@1_205_50@2_205_50@"
            logger.error("lightning")
            my_od -= 375
        elif "206" in magic_in:
            inu += "0_206_150@1_206_150@"
            logger.error("chain lightning")
            my_od -= 275
        else:
            inu	+= "0_3_5@1_3_5@2_3_5@"
            logger.error("dable spirit")
            my_od -= 345
    return {"inu": inu, "ina": ina, "inb": inb}


def zombie_warrior(my_od, fight_pm):
    inb = ""
    inu = ""
    ina = ""
    # if my_od >= 375:
    #     inu = "0_3_5@"
    list_hits = []
    data = {"count_hit": 0}
    simple = int(fight_pm)
    pinpoint = simple +20
    stable_warrior_hits = {
        'name': [
            "Простой", "Прицельный"
        ],
        'code': [0, 1],
        'mp_cost': [0, 0],
        'od': [simple, pinpoint]
    }
    stable_warrior_hits_df = pd.DataFrame(stable_warrior_hits)
    data_simple_hit = get_simple_warrior_hit(data, stable_warrior_hits_df, my_od, list_hits)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_warrior_hits_df)
    return {"inu": inu, "ina": ina, "inb": inb}


def zombie_mag(my_od):
    inb = ""
    inu = ""
    ina = ""
    list_hits = []
    data = {"count_hit": 0}
    stable_mag_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [5, 5],
        'od': [90, 50]
    }
    stable_mag_hits_df = pd.DataFrame(stable_mag_hits)
    data_simple_hit = get_simple_mag_hit(data, stable_mag_hits_df, my_od, list_hits)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_mag_hits_df)
    return {"inu": inu, "ina": ina, "inb": inb}


def paladin_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, all_my_hp, od_hit):
    ina = ""
    inb = ""
    inu = ""
    small_heal = Decimal(all_my_hp) * Decimal(0.76)
    big_heal = Decimal(all_my_hp) * Decimal(0.4)
    need_heel = Decimal(all_my_hp) * Decimal(0.2)
    if my_hp <= need_heel:
        logger.error(f" my_hp <= need_heel  {my_hp} <= {need_heel}")
        ina += "385@388@"
        my_od -= 120
    elif my_hp <= big_heal:
        logger.error(f" my_hp <= need_heel  {my_hp} <= {need_heel}")
        ina += "388@"
        my_od -= 70
    elif my_hp <= small_heal:
        logger.error(f" my_hp <= small_heal  {my_hp} <= {small_heal}")
        ina += "385@"
        my_od -= 50
    if my_od <= 70:
        if my_mp < 100:
            logger.info(" my_mp < 100")
            ina = f"521_{alchemy[0]}@"
            my_od -= 30
    if my_od >= 345:
        inu	+= "0_1_0@1_1_0@2_1_0@"
        my_od -= (Decimal(od_hit) + 20) * 3 + 75
    elif my_od >= 305:
        inu	+= "0_1_0@1_1_0@2_0_0@"
        my_od -= (Decimal(od_hit) + 20) * 2 + 75 + Decimal(od_hit)
    elif my_od >= 200:
        inu	+= "0_1_0@1_1_0@"
        my_od -= (Decimal(od_hit) + 20) * 2 + 25
    elif my_od >= 165:
        inu	+= "0_1_0@1_0_0@"
        my_od -= Decimal(od_hit) + 20 + 25 + Decimal(od_hit)
    elif my_od >= 125:
        inu	+= "0_0_0@1_0_0@"
        my_od -= Decimal(od_hit) * 2 + 25
    elif my_od >= 90:
        inu	+= "0_1_0@"
        my_od -= Decimal(od_hit) + 20
    elif my_od >= 50:
        inu	+= "0_0_0@"
        my_od -= Decimal(od_hit)
    elif my_od >= 35:
        inb	+= "0_4_0"
        my_od -= 35
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_paladin_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    ina = ""
    inb = ""
    inu = ""
    if my_hp < small_heal:
        logger.error(f" my_hp < small_heal  {my_hp} < {small_heal}")
        ina += "320@"
        my_od -= 30
    if my_mp < 500:
        logger.info(" my_mp < 500")
        ina = f"521_{alchemy[0]}@"
        inu	+= "0_3_5@1_3_5@2_2_5@"
        my_od -= 335
    inu	+= "0_3_5@1_3_5@2_3_5@"
    my_od -= 345
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_paladin_mag(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    ina = "320@"
    inb = ""
    inu = ""
    my_od -= 30
    need_mp = 1000
    # logger.debug(f"before use_mp my_od - {my_od}")
    use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = use_mp_data['ina']
    my_od = use_mp_data['my_od']
    list_hits = []
    data = {"count_hit": 0}
    stable_mag_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [300, 300],
        'od': [90, 50]
    }
    stable_mag_hits_df = pd.DataFrame(stable_mag_hits)
    data_simple_hit = get_simple_mag_hit(data, stable_mag_hits_df, my_od, list_hits)
    my_od = data_simple_hit['my_od']
    list_hits = data_simple_hit['hits']
    inu = get_query(list_hits, stable_mag_hits_df)
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_paladin(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    ina = ""
    inb = ""
    inu = ""
    if my_hp < small_heal:
        logger.error(f" my_hp < small_heal  {my_hp} < {small_heal}")
        ina += "320@"
        my_od -= 30
    if my_mp < 500:
        logger.info(" my_mp < 500")
        ina = f"521_{alchemy[0]}@"
        inu	+= "0_3_5@1_3_5@2_2_5@"
        my_od -= 335
    inu	+= "0_3_5@1_3_5@2_3_5@"
    my_od -= 345
    return {"inu": inu, "ina": ina, "inb": inb}


def small_guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy, param_lvl, my_hp, small_heal):
    ina = ""
    inb = ""
    inu = ""
    if my_hp < small_heal:
        logger.error(f" my_hp < small_heal  {my_hp} < {small_heal}")
        ina += "320@"
        my_od -= 30
    if my_od <= 70:
        if my_mp < 500:
            logger.info(" my_mp < 500")
            ina = f"521_{alchemy[0]}@"
            my_od -= 30
    if my_od >= 345:
        inu	+= "0_3_5@1_3_5@2_3_5@"
        my_od -= 345
    elif my_od >= 305:
        inu	+= "0_3_5@1_3_5@2_2_5@"
        my_od -= 305
    elif my_od >= 205:
        inu	+= "0_3_5@1_3_5@"
        my_od -= 205
    elif my_od >= 165:
        inu	+= "0_3_5@1_2_5@"
        my_od -= 165
    elif my_od >= 125:
        inu	+= "0_2_5@1_2_5@"
        my_od -= 125
    elif my_od >= 90:
        inu	+= "0_3_5@"
        my_od -= 90
    elif my_od >= 50:
        inu	+= "0_2_5@"
        my_od -= 50
    elif my_od >= 35:
        inb	+= "0_4_0"
        my_od -= 35
    return {"inu": inu, "ina": ina, "inb": inb}


def small_guard_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, all_my_hp, od_hit):
    ina = ""
    inb = ""
    inu = ""
    small_heal = Decimal(all_my_hp) * Decimal(0.76)
    big_heal = Decimal(all_my_hp) * Decimal(0.4)
    need_heel = Decimal(all_my_hp) * Decimal(0.2)
    if my_hp <= need_heel:
        logger.error(f" my_hp <= need_heel  {my_hp} <= {need_heel}")
        ina += "385@388@"
        my_od -= 120
    elif my_hp <= big_heal:
        logger.error(f" my_hp <= need_heel  {my_hp} <= {need_heel}")
        ina += "388@"
        my_od -= 70
    elif my_hp <= small_heal:
        logger.error(f" my_hp <= small_heal  {my_hp} <= {small_heal}")
        ina += "385@"
        my_od -= 50

    if my_od <= 70:
        if my_mp < 100:
            logger.info(" my_mp < 100")
            ina = f"521_{alchemy[0]}@"
            my_od -= 30
    if my_od >= 345:
        inu	+= "0_1_0@1_1_0@2_1_0@"
        my_od -= (Decimal(od_hit) + 20) * 3 + 75
    elif my_od >= 305:
        inu	+= "0_1_0@1_1_0@2_0_0@"
        my_od -= (Decimal(od_hit) + 20) * 2 + 75 + Decimal(od_hit)
    elif my_od >= 200:
        inu	+= "0_1_0@1_1_0@"
        my_od -= (Decimal(od_hit) + 20) * 2 + 25
    elif my_od >= 165:
        inu	+= "0_1_0@1_0_0@"
        my_od -= Decimal(od_hit) + 20 + 25 + Decimal(od_hit)
    elif my_od >= 125:
        inu	+= "0_0_0@1_0_0@"
        my_od -= Decimal(od_hit) * 2 + 25
    elif my_od >= 90:
        inu	+= "0_1_0@"
        my_od -= Decimal(od_hit) + 20
    elif my_od >= 50:
        inu	+= "0_0_0@"
        my_od -= Decimal(od_hit)
    elif my_od >= 35:
        inb	+= "0_4_0"
        my_od -= 35
    return {"inu": inu, "ina": ina, "inb": inb}


def guard_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, param_lvl, my_hp, small_heal):
    if int(param_lvl) >= 27:
        logger.error(f"param_lvl - {param_lvl}")
        ina = ""
        inb = ""
        inu = ""
        if my_hp < small_heal:
            logger.error(f" my_hp < small_heal  {my_hp} < {small_heal}")
            ina += "320@"
            my_od -= 30
        # if my_mp < 500:
        #     logger.info(" my_mp < 500")
        #     ina = f"521_{alchemy[0]}@521_{alchemy[1]}@521_{alchemy[2]}@"
        #     my_od -= 90
        if my_od >= 375:
            inu	+= "0_1_0@1_1_0@"
            logger.error("dable hit")
            # my_od -= 125
        elif my_od >= 120:
            inu	+= "0_1_0@"
            logger.error("hit")
            # my_od -= 90
    else:
        ina = "320@"
        inb = ""
        inu = ""
        my_od -= 30
        if my_mp < 500:
            logger.error("NEED TO STOP my_mp < 500")
        inu	+= "0_1_0@1_1_0@2_1_0@"
        my_od -= 345
    return {"inu": inu, "ina": ina, "inb": inb}


def guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy, param_lvl, my_hp, small_heal):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"bots so much - {hp_bots}")
        # for hp_bot in hp_bots:
        #     if int(hp_bot) < 2500:
        #         logger.error("bot HP < 2500")
        #         if "206" in magic_in:
        #             magic_in.remove("206")
        #         if "269" in magic_in:
        #             magic_in.remove("269")
    if int(param_lvl) >= 27:
        logger.error(f"param_lvl - {param_lvl}")
        ina = ""
        inb = ""
        inu = ""
        if my_hp < small_heal:
            logger.error(f" my_hp < small_heal  {my_hp} < {small_heal}")
            ina += "320@"
            my_od -= 30
        if my_mp < 500:
            logger.info(" my_mp < 500")
            ina = f"521_{alchemy[0]}@521_{alchemy[1]}@521_{alchemy[2]}@"
            my_od -= 90
        if my_od >= 375:
            if "242" in magic_in:
                ina += "242@"
                logger.error("magic")
                my_od -= 100
            if "206" in magic_in:
                inu += "0_206_150@1_206_150@"
                logger.error("chain lightning")
                my_od -= 275
            elif "207" in magic_in:
                inu += "0_207_75@1_207_75@2_207_75@"
                logger.error("anger")
                my_od -= 375
            elif "208" in magic_in:
                inu += "0_208_100@1_208_100@2_208_100@"
                logger.error("storm")
                my_od -= 375
            elif "205" in magic_in:
                inu += "0_205_50@1_205_50@2_205_50@"
                logger.error("lightning")
                my_od -= 375
            else:
                inu	+= "0_3_5@1_3_5@2_3_5@"
                logger.error("dable spirit")
                my_od -= 345
        elif my_od >= 150:
            # if "242" in magic_in:
            #     ina += "242@"
            #     logger.error("magic")
            #     my_od -= 100
            # if "206" in magic_in:
            #     inu += "0_206_150@"
            #     logger.error("chain lightning")
            #     my_od -= 125
            # elif "207" in magic_in:
            #     inu += "0_207_75@"
            #     logger.error("anger")
            #     my_od -= 100
            # elif "208" in magic_in:
            #     inu += "0_208_100@"
            #     logger.error("storm")
            #     my_od -= 100
            # elif "205" in magic_in:
            #     inu += "0_205_50@"
            #     logger.error("lightning")
            #     my_od -= 100
            # else:
            #     inu	+= "0_2_5@1_2_5@"
            #     logger.error("dable spirit")
            #     my_od -= 125
            inu	+= "0_2_5@1_2_5@"
            logger.error("dable spirit")
            my_od -= 125
        elif my_od >= 120:
            inu	+= "0_3_5@"
            logger.error("spirit")
            my_od -= 90
    else:
        ina = "320@"
        inb = ""
        inu = ""
        my_od -= 30
        if my_mp < 500:
            logger.error("NEED TO STOP my_mp < 500")
        inu	+= "0_3_5@1_3_5@2_3_5@"
        my_od -= 345
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
    # for priroda
    # text = f"bot level lives_g1 - '{param_en[5]}' HP - '{lives_g1[2]}' - \
    #     OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    # for dange
    text = f"bot level lives_g2 - '{param_en[5]}' HP - '{lives_g2[2]}' - \
        OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    logger.error(text)
    my_od = Decimal(fight_pm[1])
    # small_heal = Decimal(param_ow[2]) * Decimal(0.76)
    small_heal = Decimal(param_ow[2]) * Decimal(0.45)
    big_heal = Decimal(param_ow[2]) * Decimal(0.4)
    need_heel = Decimal(param_ow[2]) * Decimal(0.2)
    my_mp = Decimal(param_ow[3])
    my_hp = Decimal(param_ow[1])
    # logger.debug(f"param_en[0 - {param_en[0]}")
    if param_en[0] == "Огр-защитник":
        logger.debug("orc 25")
        data = orc_25_hunter(lives_g1, magic_in, my_od, my_mp, alchemy, fight_pm[2])
        # data = orc_25(lives_g1, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Огр-берсеркер":
        # logger.debug("orc 24")
        data = orc_24(lives_g1, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Архипаладин Мортиуса":
        logger.debug("arhi_paladin")
        data = arhi_paladin_mag(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal)
        # data = arhi_paladin_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal)
        # data = arhi_paladin(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, small_heal)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Архилич":
        logger.debug("arhi_lich")
        data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        # data = arhi_lich_warrior(lives_g2, magic_in, my_od, my_mp, alchemy)
        # data = arhi_lich(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Чумной зомби":
        logger.debug("zombie")
        data = zombie_mag(my_od)
        # data = zombie_warrior(my_od, fight_pm[2])
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Страж мавзолея":
        logger.debug("guard")
        # data = guard_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, param_en[5], my_hp, small_heal)
        data = guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy, param_en[5], my_hp, small_heal)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Страж крипты":
        logger.debug("small_guard")
        # data = small_guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy, param_en[5], my_hp, small_heal)
        data = small_guard_for_warrior(lives_g2, magic_in, my_od, my_mp, alchemy, my_hp, param_ow[2], fight_pm[2])
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
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


# @logger.catch()
# @my_timer("parse_fight")
def parse_fight(soup):
    """
    Составляем запрос на удар и лечение если требуется
    В будущем допилю список ударов пока двойно простой удар голова торс
    """
    elementos = soup.find(language="JavaScript")
    # logger.info(f"------elementos-------\n{elementos}")
    text = str(elementos).split('\n')
    # logger.info(f"------text-------\n{text}")
    # if text[1] == 'var pg_id = 3;\r':
    #     logger.info(f"------Шахта-------\n{text[1]}")
    # logger.debug(f"len text - {len(text)}")
    if len(text) == 9:
        # logger.info('end battle')
        # logger.debug(f"len text end battle - {len(text)}")
        data = parse_end_battle(text)
        return data
    # logger.debug("fight")
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
    # log = text[14].replace('var logs = ', '').replace('];', '')\
    #     .replace('"', '').replace('[', '').split(",")
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


# @my_timer("fighting")
def fighting(connect, html, fight=True):
    # logger.info("-------start fight-------")
    if fight:
        number_iteration = 0
        while fight:
            data = stop_or_hit(connect, html)
            html = data['html']
            fight = data['stop']
            number_iteration += 1
            # logger.info(f"number_iteration fight=True \
            #     {number_iteration} fight= {fight}")
    else:
        number_iteration = 0
        while number_iteration < 1:
            data = stop_or_hit(connect, html)
            html = data['html']
            fight = data['stop']
            if not fight:
                number_iteration = 100
            number_iteration += 1
            # logger.info(f"number_iteration fight=False {number_iteration}")
    return html


def stop_or_hit(connect, html):
    """
    Проверяем закончен ли бой
    """
    soup = get_data(html)
    data = parse_fight(soup)
    url = config.URL_MAIN
    if "post_id" in data.keys():
        # logger.info("post request for hit")
        html = post_html(connect, url, config.HEADER, config.PROXYES, data)
        stop = True
    else:
        logger.info("get a request for the end battle")
        html = get_html(connect, url, config.HEADER, config.PROXYES, data)
        stop = False
    return {"html": html, "stop": stop}


# @my_timer("main")
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
    main()
