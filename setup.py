import os
import sys
import numpy as np
import pandas as pd
import scipy.stats as sps
import datetime as dt
import xlwings as xw
import matplotlib.pyplot as plt
import matplotlib.style
from time import sleep

matplotlib.style.use("Solarize_Light2")
plt.rcParams["font.sans-serif"] = ["SimSun"]  # 用来正常显示中文标签

fd = {
    "family": "serif",
    "style": "normal",
    "weight": "bold",
    "size": 10
}

pd.set_option("display.width", 0)
pd.set_option("display.float_format", "{:.2f}".format)

ROOT_DIR = os.path.join("/Works", "Trade", "Reports")
INPUT_DIR = os.path.join(ROOT_DIR, "input")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates", "clean")
INTERMEDIARY_DIR = os.path.join(ROOT_DIR, "intermediary")

INSTRUMENT_INFO_DIR = os.path.join("/Database", "Futures")
CALENDAR_DIR = os.path.join("/Database", "Calendar")
MAJOR_RETURN_DIR = os.path.join(INSTRUMENT_INFO_DIR, "by_instrument", "major_return")

EXCHANGE_ID_ENG = {
    "CFFEX": "CFE",
    "DCE": "DCE",
    "SHFE": "SHF",
    "CZCE": "CZC",
    "SZ": "SZ",
    "SH": "SH",
}
EXCHANGE_ID_CHS = {
    "中金所": "CFE",
    "大商所": "DCE",
    "上期所": "SHF",
    "郑商所": "CZC",
    "深交所": "SZ",
    "上交所": "SH",
}

CHS_NAME_MAPPER = {
    # --- SHFE
    "cu": "铜",
    "al": "铝",
    "zn": "锌",
    "pb": "铅",
    "sn": "锡",
    "ni": "镍",
    "ru": "橡胶",
    "rb": "螺纹钢",
    "hc": "热卷",
    "ss": "不锈钢",
    "au": "黄金",
    "ag": "白银",
    "bu": "沥青",
    "fu": "燃油",
    "sc": "原油",
    "lu": "低硫燃料油",
    "nr": "20号胶",

    # --- DCE
    "jd": "鲜鸡蛋",
    "p": "棕榈油",
    "y": "豆油",
    "m": "豆粕",
    "a": "黄大豆一号",
    "c": "玉米",
    "cs": "玉米淀粉",
    "i": "铁矿石",
    "j": "焦炭",
    "jm": "焦煤",
    "l": "塑料",
    "v": "聚氯乙烯",
    "pp": "聚丙烯",
    "eg": "乙二醇",
    "eb": "苯乙烯",

    # --- CZCE
    "MA": "甲醇",
    "TA": "PTA",
    "CF": "棉花",
    "CY": "棉纱",
    "FG": "玻璃",
    "SR": "白糖",
    "RM": "菜粕",
    "OI": "菜籽油",
    "AP": "苹果",
    "CJ": "红枣",
    "SA": "纯碱",
    "UR": "尿素",
    "ZC": "动力煤",
}
