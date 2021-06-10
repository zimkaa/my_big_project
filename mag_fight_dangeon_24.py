from decimal import Decimal
import pandas as pd
# import requests
from time import sleep, perf_counter

from loguru import logger

import config
from request_to_nl import (
    get_html, get_data, log_in, my_ip, post_html, set_session)


def parse_end_battle(soup: object) -> dict:
    """
    Create 'data' qery to end battle
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
        "sum2": fexp[13],
    }
    return data


def use_mp(magic_in: list, alchemy: list, my_mp: Decimal,
           ina: str, my_od: Decimal, mp_need: int) -> dict:
    """
    Restore MP
    """
    not_alchemy = [
        "279", "277", "207", "242", "208", "205", "206", "269",
        "270", "320", '375', '376', '381', '382', '477', '478',
        '479', '483', '482', '265', '266',
    ]
    magic = []
    for obj in magic_in:
        if obj not in not_alchemy:
            magic.append(obj)
    if not magic:
        return {"ina": ina, "my_od": my_od}
    dict_name_boost_mp = {
        'name': [
            "Тыквенное зелье", "Превосходное Зелье Маны",
            "Восстановление MP", "Зелье Восстановления Маны",
        ],
        'code': [337, 521, 33, 306],
        'priority': [0, 1, 2, 3],
        'mp_boost': [999, 500, 500, 100],
        'od': [30, 30, 30, 30],
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
    sorted_list_df = new_df.sort_values(by='priority')
    if my_mp <= mp_need:
        logger.info("---------------Use MP--------------------")
        boost_mp = 0
        query_mp = ""
        for index in sorted_list_df.index:
            boost_mp += int(sorted_list_df['mp_boost'][index])
            query_mp = sorted_list_df['query'][index]
            condition = int(boost_mp) - mp_need
            my_od -= int(sorted_list_df['od'][index])
            if condition >= 0 and my_od <= 30:
                ina += query_mp
                break
            else:
                ina += query_mp
        logger.info(f"ina _ mp - {ina}")
    return {"ina": ina, "my_od": my_od}


def check_hit(data: dict[str, int], my_od: Decimal,
              new_df: object, list_hits: list) -> dict:
    """
    Check git
    """
    for _ in range(data['count_hit']):
        list_hits.append(new_df['code'][2])
        my_od -= new_df['od'][2]
    my_od -= data['use_od']
    return {"my_od": my_od, "hits": list_hits}


def get_hit(magic_in: list, inu: str, my_od: Decimal) -> dict:
    """
    Create hits
    """
    hits = {
        'name': [
            "Гнев Титанов",
            "Ураган", "Молния",
        ],
        'code': [207, 208, 205],
        'mp_cost': [75, 100, 50],
        'od': [100, 100, 100],
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
            "Mind Blast", "Spirit Arrow",
        ],
        'code': [3, 2],
        'mp_cost': mp_cost,
        'od': [90, 50],
    }
    stable_hits_df = pd.DataFrame(stable_hits)
    logger.debug(f"list_element - {list_element} len - {len(list_element)}")
    for name in list_element:
        result = hits_df[hits_df['code'] == name]
        stable_hits_df = stable_hits_df.append(result, ignore_index=True)
    list_hits = []
    for _ in stable_hits_df.index[2:]:
        if my_od >= 375:
            count = 3
            use_od = 25 * count
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        elif my_od >= 225:
            count = 2
            use_od = 25 * (count - 1)
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        elif my_od >= 100:
            count = 1
            use_od = 25 * (count - 1)
            data = {"count_hit": count, "use_od": use_od}
            result_data = check_hit(data, my_od, stable_hits_df, list_hits)
            my_od = result_data['my_od']
            list_hits = result_data['hits']
            break
        else:
            data = {"count_hit": 0}
            break
    else:
        data = {"count_hit": 0}
    data_simple_hit = get_simple_mag_hit(data, my_od, stable_hits_df)
    my_od = data_simple_hit['my_od']
    new_list_hits = data_simple_hit['hits']
    list_hits += new_list_hits
    inu = get_query(list_hits, stable_hits_df)
    return {"inu": inu, "my_od": my_od}


def get_simple_mag_hit(data: dict[str, int],
                       my_od: Decimal, df: object) -> dict:
    """
    Get simple mag hit
    """
    list_hits = []
    big_hit = int(df['od'][0])
    small_hit = int(df['od'][1])
    if data['count_hit'] == 0:
        if my_od >= (big_hit * 3 + 75):
            list_hits = [df['code'][0] for _ in range(3)]
            my_od -= big_hit * 3 + 75
        elif my_od >= (big_hit * 2 + 75 + small_hit):
            list_hits = [df['code'][0] for _ in range(2)]
            list_hits.append(df['code'][1])
            my_od -= big_hit * 2 + small_hit + 75
        elif my_od >= (big_hit + 75 + small_hit * 2):
            list_hits = [df['code'][1] for _ in range(2)]
            list_hits.append(df['code'][0])
            my_od -= big_hit + small_hit * 2 + 75
        elif my_od >= (75 + small_hit * 3):
            list_hits = [df['code'][1] for _ in range(3)]
            my_od -= small_hit * 3 + 75
        elif my_od >= (big_hit * 2 + 25):
            list_hits = [df['code'][0] for _ in range(2)]
            my_od -= big_hit * 2 + 25
        elif my_od >= (big_hit + small_hit + 25):
            list_hits.append(df['code'][0])
            list_hits.append(df['code'][1])
            my_od -= big_hit + small_hit + 25
        elif my_od >= (small_hit * 2 + 25):
            list_hits = [df['code'][1] for _ in range(2)]
            my_od -= small_hit * 2 + 25
        elif my_od >= big_hit:
            list_hits.append(df['code'][0])
            my_od -= big_hit
        elif my_od >= small_hit:
            list_hits.append(df['code'][1])
            my_od -= small_hit
    elif data['count_hit'] == 1:
        if my_od >= (big_hit * 2 + 75):
            list_hits = [df['code'][0] for _ in range(2)]
            my_od -= big_hit * 2 + 75
        elif my_od >= (big_hit + small_hit + 75):
            list_hits.append(df['code'][0])
            list_hits.append(df['code'][1])
            my_od -= big_hit + small_hit + 75
        elif my_od >= (small_hit * 2 + 75):
            list_hits = [df['code'][1] for _ in range(2)]
            my_od -= small_hit * 2 + 75
        elif my_od >= (big_hit + 25):
            list_hits.append(df['code'][0])
            my_od -= big_hit + 25
        elif my_od >= (small_hit + 25):
            list_hits.append(df['code'][1])
            my_od -= small_hit + 25
    elif data['count_hit'] == 2:
        if my_od >= (big_hit + 75):
            list_hits.append(df['code'][0])
            my_od -= big_hit + 75
        elif my_od >= (small_hit + 75):
            list_hits.append(df['code'][1])
            my_od -= small_hit + 75
    return {"my_od": my_od, "hits": list_hits}


def get_query(list_hits: list, df: object) -> str:
    """
    Create query part 'inu'
    """
    inu = ""
    for num, value in enumerate(list_hits):
        mp_cost = df[df['code'] == value].iloc[0]['mp_cost']
        inu += f"{num}_{value}_{mp_cost}@"
    return inu


def arhi_lich_mag(lives_g2: list, magic_in: list, my_od: Decimal,
                  my_mp: Decimal, alchemy: list) -> dict:
    """
    Fight with arhilich
    """
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    logger.error(f"hp_bots - {hp_bots}")

    inb = ""
    inu = ""
    ina = ""
    # ina = "320@"
    # my_od -= 30

    """HEAL MP!!!"""
    # need_mp = 100
    # use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    # ina = use_mp_data['ina']
    # my_od = use_mp_data['my_od']
    # if my_mp < 100:
    #     logger.error("NEED TO STOP my_mp < 100")
    #     error = Exception(" NEED TO STOP my_mp < 100 MPPPP!!!!")
    #     raise error

    if my_od >= 170:
        if "242" in magic_in:
            ina += "242@"
            my_od -= 100
    get_hit_data = get_hit(magic_in, inu, my_od)
    inu = get_hit_data['inu']
    my_od = get_hit_data['my_od']

    return {"inu": inu, "ina": ina, "inb": inb}


def arhi_lich_mag_2(lives_g2: list, magic_in: list, my_od: Decimal,
                    my_mp: Decimal, alchemy: list) -> dict:
    """
    Fight with arhilich V2
    """
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    if len(hp_bots) > 1:
        logger.error(f"priziv - {hp_bots}")
    logger.error(f"hp_bots - {hp_bots}")
    ina = ""
    inb = ""
    inu = ""

    """HEAL MP!!!"""
    # need_mp = 100
    # use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    # ina = use_mp_data['ina']
    # my_od = use_mp_data['my_od']
    # if my_mp < 100:
    #     logger.error("NEED TO STOP my_mp < 100")
    #     error = Exception(" NEED TO STOP my_mp < 100 MPPPP!!!!")
    #     raise error

    if my_mp >= 1000:
        if my_od >= 170:
            if "242" in magic_in:
                ina += "242@"
                my_od -= 100
        mo_cost = int(my_mp / 3)
        if mo_cost >= 300:
            mo_cost = 300
        stable_mag_hits = {
            'name': [
                "Mind Blast", "Spirit Arrow",
            ],
            'code': [3, 2],
            'mp_cost': [mo_cost, mo_cost],
            'od': [90, 50],
        }
        df = pd.DataFrame(stable_mag_hits)
        data_simple_hit = get_simple_hit(my_od, df)
    else:
        stable_mag_hits = {
            'name': [
                "Mind Blast", "Spirit Arrow",
            ],
            'code': [3, 2],
            'mp_cost': [5, 5],
            'od': [90, 50],
        }
        df = pd.DataFrame(stable_mag_hits)
        data_simple_hit = get_simple_hit(my_od, df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)
    return {"inu": inu, "ina": ina, "inb": inb}


def zombie_mag(my_od: Decimal, my_mp: Decimal, fight_pm: str) -> dict:
    """
    Fight with zombie
    """
    ina = ""
    inb = ""
    inu = ""
    simple = int(fight_pm)
    pinpoint = simple + 20
    stable_warrior_hits = {
        'name': [
            "Прицельный", "Простой",
        ],
        'code': [1, 0],
        'mp_cost': [0, 0],
        'od': [pinpoint, simple],
    }
    stable_warrior_hits_df = pd.DataFrame(stable_warrior_hits)
    data_simple_hit = get_simple_warrior_hit(my_od, stable_warrior_hits_df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, stable_warrior_hits_df)
    return {"inu": inu, "ina": ina, "inb": inb}


def get_simple_warrior_hit(my_od: Decimal, df: object) -> dict:
    """
    Create posible warrior hit dict
    """
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


def arhi_paladin_mag(lives_g2: list, magic_in: list, my_od: Decimal,
                     my_mp: Decimal, alchemy: list, fight_pm: str) -> dict:
    """
    Fight with arhipaladin
    """
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
    inb = ""
    inu = ""
    ina = ""
    # ina = "320@"
    # my_od -= 30

    """HEAL MP!!!"""
    # need_mp = 100
    # use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    # ina = use_mp_data['ina']
    # my_od = use_mp_data['my_od']
    if my_mp < 15:
        logger.error("NEED TO STOP my_mp < 15")
        error = Exception(" NEED TO STOP my_mp < 15 MPPPP!!!!")
        raise error

    if my_od >= 170 and my_mp > 1000:
        if "242" in magic_in:
            ina += "242@"
            my_od -= 100

    if my_mp >= 15:
        mo_cost = int(my_mp / 3)
        if mo_cost >= 300:
            mo_cost = 300
        stable_mag_hits = {
            'name': [
                "Mind Blast", "Spirit Arrow",
            ],
            'code': [3, 2],
            'mp_cost': [mo_cost, mo_cost],
            'od': [90, 50],
        }
        df = pd.DataFrame(stable_mag_hits)
        data_simple_hit = get_simple_hit(my_od, df)
    else:
        simple = int(fight_pm)
        pinpoint = simple + 20
        stable_warrior_hits = {
            'name': [
                "Прицельный", "Простой",
            ],
            'code': [1, 0],
            'mp_cost': [0, 0],
            'od': [pinpoint, simple],
        }
        df = pd.DataFrame(stable_warrior_hits)
        data_simple_hit = get_simple_warrior_hit(my_od, df)

    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)
    return {"inu": inu, "ina": ina, "inb": inb}


def get_simple_hit(my_od: Decimal, df: object) -> dict:
    """
    Create simple hit
    """
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


def guard_for_mag(lives_g2: list, magic_in: list, my_od: Decimal,
                  my_mp: Decimal, alchemy, fight_pm: str,
                  my_all_mp: Decimal, my_hp: Decimal,
                  my_all_hp: Decimal) -> dict:
    """
    Fight with guard
    """
    max_number_iter = int(len(lives_g2) / 5)
    number_iter = 2
    hp_bots = []
    for _ in range(max_number_iter):
        hp_bots.append(lives_g2[number_iter])
        number_iter += 5
    logger.error(f"bots HP - {hp_bots}")
    if my_hp < (my_all_hp * Decimal(0.75)):
        ina = "320@"
        my_od -= 30
    else:
        ina = ""
    inb = ""

    """HEAL MP!!!"""
    need_mp = 100
    data_ues_mp = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    ina = data_ues_mp['ina']
    my_od = data_ues_mp['my_od']
    # if my_mp < 100:
    #     logger.error("NEED TO STOP my_mp < 100")
    #     error = Exception(" NEED TO STOP my_mp < 100 MPPPP!!!!")
    #     raise error

    min_mp = my_all_mp * Decimal(0.01)
    # logger.error(f"min_mp - {min_mp}")
    # if my_mp > 4000:
    if my_mp > min_mp:
        stable_mag_hits = {
            'name': [
                "Mind Blast", "Spirit Arrow",
            ],
            'code': [3, 2],
            'mp_cost': [5, 5],
            'od': [90, 50],
        }
        df = pd.DataFrame(stable_mag_hits)
        data_simple_hit = get_simple_hit(my_od, df)
    else:
        simple = int(fight_pm)
        pinpoint = simple + 20
        stable_warrior_hits = {
            'name': [
                "Прицельный", "Простой",
            ],
            'code': [1, 0],
            'mp_cost': [0, 0],
            'od': [pinpoint, simple],
        }
        df = pd.DataFrame(stable_warrior_hits)
        data_simple_hit = get_simple_warrior_hit(my_od, df)
    list_hits = data_simple_hit['hits']
    my_od = data_simple_hit['my_od']
    inu = get_query(list_hits, df)
    return {"inu": inu, "ina": ina, "inb": inb}


def any_bot(lives_g1: list, magic_in: list, my_od: Decimal,
            my_mp: Decimal, alchemy: list, lives_g2: str) -> dict:
    """
    Fight with my attacker
    """
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
    inb = ""
    inu = ""
    # ina = ""
    ina = "320@"
    my_od -= 30

    """HEAL MP!!!"""
    # need_mp = 1000
    # use_mp_data = use_mp(magic_in, alchemy, my_mp, ina, my_od, need_mp)
    # ina = use_mp_data['ina']
    # my_od = use_mp_data['my_od']
    if my_mp < 100:
        logger.error("NEED TO STOP my_mp < 100")
        error = Exception(" NEED TO STOP my_mp < 100 MPPPP!!!!")
        raise error

    if my_od >= 170:
        if "242" in magic_in:
            ina += "242@"
            my_od -= 100
    get_hit_data = get_hit(magic_in, inu, my_od)
    inu = get_hit_data['inu']
    my_od = get_hit_data['my_od']
    return {"inu": inu, "ina": ina, "inb": inb}


def logic(data: dict) -> dict:
    """
    Main logic
    """
    param_ow = data['param_ow']
    param_en = data['param_en']
    fight_pm = data['fight_pm']
    fight_ty = data['fight_ty']
    lives_g1 = data['lives_g1']
    lives_g2 = data['lives_g2']
    magic_in = data['magic_in']
    alchemy = data['alchemy']
    # logger.error(f"data \n{data}")
    # logger.error(f"param_en - {param_en}")
    # logger.error(f"param_en[1] - {param_en[1]}")
    # logger.error(f"param_ow[3] - {param_ow[3]}")
    # logger.error(f"fight_pm[1] - {fight_pm[1]}")
    # logger.error(f"param_ow[1] - {param_ow[1]}")
    # {param_en[0]}
    # name = param_en[0].encode('utf-8')
    name = ""
    # logger.error(f"param_en[0] - {param_en[0]}")
    text = f"name {name} bot level lives_g2 - '{param_en[5]}' HP - '{param_en[1]}' - \
        OD - '{fight_pm[1]}' MP - '{param_ow[3]}' HP - '{param_ow[1]}'"
    logger.error(text)
    my_od = Decimal(fight_pm[1])
    my_mp = Decimal(param_ow[3])
    my_all_mp = Decimal(param_ow[4])
    my_hp = Decimal(param_ow[1])
    my_all_hp = Decimal(param_ow[2])
    if param_en[0] == "Архипаладин Мортиуса":
        logger.debug("arhi_paladin")
        data = arhi_paladin_mag(lives_g2, magic_in, my_od,
                                my_mp, alchemy, fight_pm[2])
        # data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        # data = arhi_lich_mag_2(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Паладин Мортиуса":
        logger.debug("paladin")
        data = arhi_paladin_mag(lives_g2, magic_in, my_od,
                                my_mp, alchemy, fight_pm[2])
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Архилич":
        logger.debug("arhi_lich")
        # data = arhi_lich_mag(lives_g2, magic_in, my_od,
        #                      my_mp, alchemy, fight_pm[2])
        data = arhi_lich_mag_2(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Лич":
        logger.debug("arhi_lich")
        data = arhi_lich_mag_2(lives_g2, magic_in, my_od, my_mp, alchemy)
        # data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Чумной зомби":
        logger.debug("zombie")
        data = zombie_mag(my_od, my_mp, fight_pm[2])
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Страж мавзолея":
        logger.debug("guard")
        data = guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy,
                             fight_pm[2], my_all_mp, my_hp, my_all_hp)
        # data = arhi_lich_mag_2(lives_g2, magic_in, my_od, my_mp, alchemy)
        # data = arhi_lich_mag(lives_g2, magic_in, my_od, my_mp, alchemy)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    elif param_en[0] == "Страж крипты":
        logger.debug("small_guard")
        data = guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy,
                             fight_pm[2], my_all_mp, my_hp, my_all_hp)
        ina = data["ina"]
        inb = data["inb"]
        inu = data["inu"]
    else:
        logger.debug("any_bot")
        # data = guard_for_mag(lives_g2, magic_in, my_od, my_mp, alchemy,
        #                      fight_pm[2], my_all_mp, my_hp, my_all_hp)
        data = any_bot(lives_g1, magic_in, my_od, my_mp, alchemy, lives_g2)
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
        "ina": ina,
    }
    logger.debug(f"vcode {data['vcode']}")
    return data


def parse_fight(soup: object) -> dict:
    """
    Processing 'data'
    """
    elementos = soup.find(language="JavaScript")
    # logger.debug(f"elementos {elementos}")
    text = str(elementos).split('\n')
    if len(text) == 9:
        data = parse_end_battle(text)
        return data
    # logger.debug(f"text {text}")
    # logger.debug(f"text[9] {text[9]}")

    # fight_ty = text[1].replace('var fight_ty = ', '').replace('];', '')\
    #     .replace('"', '').replace('[', '').split(",")
    # param_ow = text[2].replace('var param_ow = ', '').replace('];', '')\
    #     .replace('"', '').replace('[', '').split(",")
    # param_en = text[8].replace('var param_en = ', '').replace('];', '')\
    #     .replace('"', '').replace('[', '').split(",")
    # fight_pm = text[11].replace('var fight_pm = ', '').replace('];', '')\
    #     .replace('"', '').replace('[', '').split(",")
    # lives_g1 = text[4].replace('var lives_g1 = ', '').replace(';', '')\
    #     .replace('"', '').replace('[', '').replace(']', '').split(",")
    # lives_g2 = text[5].replace('var lives_g2 = ', '').replace(';', '')\
    #     .replace('"', '').replace('[', '').replace(']', '').split(",")
    # alchemy = text[6].replace('var stand_in = ', '')\
    #     .replace('[', '').replace('];', '').split(",")
    # magic_in = text[7].replace('var magic_in = ', '').replace(';', '')\
    #     .replace('[', '').replace(']', '').split(",")

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
        "alchemy": alchemy,
    }
    data = logic(data_to_fight)
    return data


def fighting(connect: object, html: object, fight: bool = True) -> object:
    """
    Fight while
    """
    if fight:
        number_iteration = 0
        while fight:
            data = stop_or_hit(connect, html)
            html = data['html']
            fight = data['stop']
            number_iteration += 1
            logger.info(f"fight_iteration - '{number_iteration}'")
            if number_iteration >= 500:
                # requests.get("https://armorwp.com/custom.php?text=TOO_LONG_FIGHT_TURN")
                error = Exception("----TOO LONG FIGHT----")
                raise error
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


def stop_or_hit(connect: object, html: object) -> dict:
    """
    Stop or hit
    """
    # logger.error(f"html  ---\n{html.text}")
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


def main2():
    ip = my_ip(config.PROXYES)
    logger.info(f"-------ip------- {ip}")
    if config.PROXY_IP in ip:
        logger.info("ip IS proxy YES")
        connect = set_session()
        html = log_in(connect)
        game = True
        iteration = 0
        logger.info(f"iteration {iteration}")
        while game:
            start_iter = perf_counter()
            if html.text.find("div") != -1:
                # start = perf_counter()
                # soup = get_data(html)
                # ex_time = perf_counter() - start
                # logger.info(f"Execution time get_data {ex_time}")

                # start = perf_counter()
                # data = soup.find('div')
                # ex_time = perf_counter() - start
                # logger.info(f"Execution time soup.find('div') {ex_time}")
                # if data:
                # logger.info(f"soup.find('div') {soup.find('div')}")
                start = perf_counter()
                # a = html.text.find('div')
                # logger.info(f"html.text.find('div') {a}")
                ex_time = perf_counter() - start
                logger.info(f"Execution time html.text.find('div') {ex_time}")
                """
                Надо написать:
                Автоюз портала и автоупивка!!!
                1) хилку
                2) одевание банок маны если нет хотябы 1й
                3) DNV тыкалку!!!
                """
            else:
                # fighting(connect, html, False)
                fighting(connect, html)
            url = config.URL + "/ch.php?0.3296457688728473&show=1&fyo=0"
            get_html(connect, url)
            # logger.info(f"chat {chat.text}")
            html = get_html(connect, config.URL_MAIN)
            sleep(15)
            iteration += 1
            ex_time = perf_counter() - start_iter
            text = f"iteration {iteration} iteration execution time {ex_time}"
            logger.info(text)
            # url = config.URL + "/ch.php?0.3296457688728473&show=1&fyo=0"
            # chat = get_html(connect, url)
            # logger.info(f"chat {chat.text}")


if __name__ == '__main__':
    logger.add(
        "fight_dangeon.log", format="{time} {level} {message}",
        level="DEBUG", rotation="24 hour", compression="zip",
    )
    main()
    # main2()
