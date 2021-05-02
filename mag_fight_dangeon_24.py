from decimal import Decimal
import pandas as pd
import requests

from loguru import logger

import config
from request_to_nl import get_html, post_html, get_data, log_in, set_session


def my_ip(proxies=None):
    """
    Получаем текущий IP сессии
    """
    answer = requests.get(config.CHECKER_IP_SITE,
                          headers=config.HEADER, proxies=proxies)
    return answer.text


def parse_end_battle(soup):
    """
    Составляем запрос на выход из боя
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
    Логика смотрит что выпить с пояса при определенном количестве маны пока жестко меньше 1к
    """
    not_alchemy = ["279", "277", "207", "242", "208", "205", "206", "269", "270", "320", '375', '376', '381', '382', '477', '478', '479', '483', '482', '265', '266']
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
    # logger.info(f"magic - {magic} len m - {len(magic)}")
    for num, element in enumerate(magic):
        element = int(element)
        for index in df.index:
            if df['code'][index] == element:
                query.append(f"{element}_{alchemy[num]}@")
                list_element.append(element)
    new_df = pd.DataFrame()
    for name in list_element:
        # result = None
        result = df[df['code'] == name]
        # if result:
        #     new_df = new_df.append(result, ignore_index=True)
        new_df = new_df.append(result, ignore_index=True)
    new_df['query'] = query
    sorted_list_df = new_df.sort_values(by='priority')
    if my_mp <= mp_need:
        logger.info("---------------Use MP--------------------")
        boost_mp = 0
        query_mp = ""
        for index in sorted_list_df.index:
            # logger.info(f"before boost_mp - {boost_mp}")
            boost_mp += int(sorted_list_df['mp_boost'][index])
            # logger.info(f"after boost_mp - {boost_mp}")
            query_mp = sorted_list_df['query'][index]
            condition = int(boost_mp) - mp_need
            # logger.info(f"before my_od - {my_od}")
            my_od -= int(sorted_list_df['od'][index])
            # logger.info(f"after my_od - {my_od}")
            if condition >= 0 and my_od <= 30:
                ina += query_mp
                break
            else:
                ina += query_mp
        logger.info(f"ina _ mp - {ina}")
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
    logger.info(f"before magic hit my_od {my_od}")
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
    mp_cost = [5, 5]
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
        'mp_cost': mp_cost,
        'od': [90, 50]
    }
    stable_hits_df = pd.DataFrame(stable_hits)
    logger.debug(f"list_element - {list_element} len - {len(list_element)}")
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
    data_simple_hit = get_simple_mag_hit(data, my_od, stable_hits_df)
    my_od = data_simple_hit['my_od']
    logger.info(f"after magic hit my_od {my_od}")
    new_list_hits = data_simple_hit['hits']
    list_hits += new_list_hits
    logger.error(f"list_hits {list_hits}")
    inu = get_query(list_hits, stable_hits_df)
    logger.info(f"inu {inu}")
    # logger.info(f"inu {inu} my_od {my_od} ")
    return {"inu": inu, "my_od": my_od}


def get_simple_mag_hit(data, my_od, df):
    list_hits = []
    big = int(df['od'][0])
    small = int(df['od'][1])
    # logger.info(f"df {df} type {type(df)} ")
    # logger.info(f"df['od'][0] {df['od'][0]} type {type(df['od'][0])} ")
    # big = df['od'][0]
    # small = df['od'][1]
    if data['count_hit'] == 0:
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
    elif data['count_hit'] == 1:
        if my_od >= (big * 2 + 75):
            list_hits = [df['code'][0] for _ in range(2)]
            my_od -= big * 2 + 75
        elif my_od >= (big + small + 75):
            list_hits.append(df['code'][0])
            list_hits.append(df['code'][1])
            my_od -= big + small + 75
        elif my_od >= (small * 2 + 75):
            list_hits = [df['code'][1] for _ in range(2)]
            my_od -= small * 2 + 75
        elif my_od >= (big + 25):
            list_hits.append(df['code'][0])
            my_od -= big + 25
        elif my_od >= (small + 25):
            list_hits.append(df['code'][1])
            my_od -= small + 25
    elif data['count_hit'] == 2:
        if my_od >= (big + 75):
            list_hits.append(df['code'][0])
            my_od -= big + 75
        elif my_od >= (small + 75):
            list_hits.append(df['code'][1])
            my_od -= small + 75
    return {"my_od": my_od, "hits": list_hits}


def get_query(list_hits, df):
    inu = ""
    for num, value in enumerate(list_hits):
        mp_cost = df[df['code'] == value].iloc[0]['mp_cost']
        inu += f"{num}_{value}_{mp_cost}@"
    return inu


# def arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy):
#     max_number_iter = int(len(lives_g2) / 5)
#     number_iter = 2
#     hp_bots = []
#     for _ in range(max_number_iter):
#         hp_bots.append(lives_g2[number_iter])
#         number_iter += 5
#     if len(hp_bots) > 1:
#         logger.error(f"priziv - {hp_bots}")
#     logger.error(f"hp_bots - {hp_bots}")
#     ina = "320@"
#     inb = ""
#     inu = ""
#     my_od -= 30
#     need_mp = 1000
#     use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
#     ina = use_mp_data['ina']
#     my_od = use_mp_data['my_od']
#     get_hit_data = get_hit(magic_in, inu, my_od)
#     inu = get_hit_data['inu']
#     my_od = get_hit_data['my_od']
#     return {"inu": inu, "ina": ina, "inb": inb}


def arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
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


def zombie_mag(my_od):
    ina = ""
    inb = ""
    inu = ""
    stable_mag_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [5, 5],
        'od': [90, 50]
    }
    df = pd.DataFrame(stable_mag_hits)
    data_simple_hit = get_simple_hit(my_od, df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)
    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_paladin_mag(lives_g2, magic_in, my_od, my_mp, alchemy):
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
    use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = use_mp_data['ina']
    my_od = use_mp_data['my_od']

    stable_mag_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [300, 300],
        'od': [90, 50]
    }
    df = pd.DataFrame(stable_mag_hits)
    data_simple_hit = get_simple_hit(my_od, df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)

    if my_mp < 100:
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        error = Exception("MPPPP!!!!")
        raise error
    return {"inu": inu, "ina": ina, "inb": inb}


def get_simple_hit(my_od, df):
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


def guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy):
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    logger.error(f"bots HP - {hp_bots}")

    ina = "320@"
    inb = ""
    my_od -= 30

    need_mp = 100     # -----------------------------------------------------
    data_ues_mp = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = data_ues_mp['ina']
    my_od = data_ues_mp['my_od']

    stable_mag_hits = {
        'name': [
            "Mind Blast", "Spirit Arrow"
        ],
        'code': [3, 2],
        'mp_cost': [5, 5],
        'od': [90, 50]
    }
    df = pd.DataFrame(stable_mag_hits)
    data_simple_hit = get_simple_hit(my_od, df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)

    if my_mp < 100:
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        logger.error("NEED TO STOP my_mp < 100")
        error = Exception("MPPPP!!!!")
        raise error

    return {"inu": inu, "ina": ina, "inb": inb}


def any_bot(lives_g1, magic_in, my_od, my_mp, alchemy, lives_g2):
    if int(len(lives_g1)) == 8:
        max_number_iter = int(len(lives_g2) / 5)
    else:
        max_number_iter = int(len(lives_g1) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g1[number_iter])
        number_iter += 5
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
    # text = f"name {name} bot level lives_g2 - '{param_en[5]}' HP - '{lives_g1[2]}' - \
    #     OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    text = f"name {name} bot level lives_g2 - '{param_en[5]}' HP - '{param_en[1]}' - \
        OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    logger.error(text)
    my_od = Decimal(fight_pm[1])
    small_heal = Decimal(param_ow[2]) * Decimal(0.45)
    big_heal = Decimal(param_ow[2]) * Decimal(0.4)
    need_heel = Decimal(param_ow[2]) * Decimal(0.2)
    my_mp = Decimal(param_ow[3])
    my_hp = Decimal(param_ow[1])
    if param_en[0] == "Архипаладин Мортиуса":
        logger.debug("arhi_paladin")
        data = arhi_paladin_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Архилич":
        logger.debug("arhi_lich")
        data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Чумной зомби":
        logger.debug("zombie")
        data = zombie_mag(my_od)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Страж мавзолея":
        logger.debug("guard")
        data = guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    else:
        logger.debug("any_bot")
        data = any_bot(lives_g1, magic_in, my_od, my_mp, alchemy, lives_g2)
        # data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
        # error = Exception("Not Dangeon")
        # raise error
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
    Составляем запрос на удар и лечение если требуется
    В будущем допилю список ударов пока двойно простой удар голова торс
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
    Проверяем закончен ли бой
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
    logger.add(
        "fight_dangeon.log", format="{time} {level} {message}",
        level="DEBUG", rotation="24 hour", compression="zip",
    )
    main()
