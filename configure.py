BGN_DATE = "20200730"

TEMPLATES_FILE_LIST = {
    "input_order_inside": "00_衍生品交易指令单_大宗商品_YYYYMMDD.xlsx",
    "input_order_outside": "01_衍生品投资管理总部交易指令单_大宗商品_YYYYMMDD.xlsx",
    "traded_order": "02_衍生品当日成交_大宗商品_YYYYMMDD.xlsx",
    "traded_order_summary": "03_衍生品当日成交汇总_大宗商品_YYYYMMDD.xlsx",
    "position_details": "04_衍生品持仓情况明细表_大宗商品_YYYYMMDD.xlsx",
    "pnl_summary": "05_衍生品盈亏情况明细表_大宗商品_YYYYMMDD.xlsx",
    "risk_control": "06_衍生品风险限额监控表_大宗商品_YYYYMMDD.xlsx",
    "report_margin": "07_衍生品交易详情日报表_大宗商品_YYYYMMDD_风控_Margin.xlsx",
    "report_no_margin": "08_衍生品交易详情日报表_大宗商品_YYYYMMDD_财务_NoMargin.xlsx",
}

nav_file = "组合净值.xlsx"

WAN_YUAN = 1E4
INIT_PREMIUM = (200 + 800 + 1000
                + 1000 + 2000 + 1000 + 1000 + 3000) * WAN_YUAN
ACCOUNT = "30216888"
PERMISSION_CODE = "见红塔证投字（2020）第27号文"

POS_PROP_SCALE = 1E4
MARGIN_RATE_SCALE = 100

SAVE_NAME_START_IDX = 0
VERSION_TAG = ""

# contracts which are not traded by us
EXCEPTION_UNIVERSE = ["IC", "IH", "IF"]

# BASE_YEAR_DATE # change it when new year has come
# BASE_YEAR_DATE = "20201231"
BASE_YEAR_DATE = "20211231"
