import numpy as np

from setup import *


def check_and_mkdir(x):
    if not os.path.exists(x):
        os.mkdir(x)
    return 0


def expand_date_format(x):
    return "{}-{}-{}".format(x[0:4], x[4:6], x[6:8])


def parse_instrument_id(t_contract_id: str):
    s = 0
    while (t_contract_id[s] < '0') or (t_contract_id[s] > '9'):
        s += 1
    return t_contract_id[0:s]


def load_input_and_traded_data(t_report_date, t_input_dir):
    _input_file = 'input.{}.csv'.format(t_report_date)
    _traded_file = 'traded.{}.csv'.format(t_report_date)
    _input_path = os.path.join(t_input_dir, t_report_date[0:4], t_report_date, _input_file)
    _traded_path = os.path.join(t_input_dir, t_report_date[0:4], t_report_date, _traded_file)
    if not os.path.exists(_input_path):
        print("There is neither input nor traded for {}".format(t_report_date))
        return None, None

    _input_df = pd.read_csv(_input_path, encoding='gb18030')
    if not os.path.exists(_traded_path):
        print("Warning! There is input data but traded data for {}".format(t_report_date))
        _input_df["qty"] = 0
        _input_df["aver_price"] = 0
        return _input_df, None

    _traded_df = pd.read_csv(_traded_path, encoding='gb18030')
    _traded_stats = {}
    for _input_code, _input_code_df in _traded_df.groupby(by="报单编号"):
        _qty = _input_code_df["成交量"].sum()
        _aver_price = np.sum(_input_code_df["成交量"] * _input_code_df["成交均价"]) / _qty
        _traded_stats[_input_code] = {"qty": _qty, "aver_price": _aver_price}
    _traded_stats_df = pd.DataFrame.from_dict(_traded_stats, orient="index")
    _input_df = _input_df.merge(right=_traded_stats_df, left_on="委托号", right_index=True, how="left")
    _traded_df = _traded_df.merge(right=_input_df[["委托号", "买卖方向", "多空方向"]], left_on="报单编号", right_on="委托号", how="left")
    return _input_df, _traded_df


def group_traded_data(t_traded_df, t_exception_universe):
    _traded_stats = {}
    t_traded_df["position"] = t_traded_df["多空方向"].map(lambda z: 1 if z in ["开多", "平多"] else -1)
    traded_selected_cols = ["合约代码", "position", "买卖方向", "成交量", "成交均价"]
    for (cid, cid_pos), cid_pos_df in t_traded_df[traded_selected_cols].groupby(by=["合约代码", "position"]):
        _instrument_id = parse_instrument_id(cid)
        if _instrument_id in t_exception_universe:
            continue

        _traded_stats[(cid, cid_pos)] = {"open": None, "close": None}
        for operation, operation_df in cid_pos_df.groupby(by="买卖方向"):
            if (cid_pos, operation) == (1, "买入"):
                _traded_stats[(cid, cid_pos)]["open"] = operation_df
                continue

            if (cid_pos, operation) == (1, "卖出"):
                _traded_stats[(cid, cid_pos)]["close"] = operation_df
                continue

            if (cid_pos, operation) == (-1, "买入"):
                _traded_stats[(cid, cid_pos)]["close"] = operation_df
                continue

            if (cid_pos, operation) == (-1, "卖出"):
                _traded_stats[(cid, cid_pos)]["open"] = operation_df
                continue

    return _traded_stats


def convert_contract_format(t_cid: str, t_eid: str, t_mapper: dict):
    _wind_cid = t_cid.upper()
    _wind_eid = t_mapper[t_eid]
    return "{}.{}".format(_wind_cid, _wind_eid)


def convert_wind_code_to_cid(t_wind_code: str):
    _wc, _market = t_wind_code.split(".")

    if _market in ["CZC", "CFE"]:
        return _wc
    else:
        return _wc.lower()


def update_r07_prev_date(t_cid, t_cid_pos, t_ws, t_s, t_src_df, t_margin_tag, t_pos_prop_scale):
    t_ws.range("D{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "qty_prev"]
    t_ws.range("E{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "settle_prev"]
    t_ws.range("G{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_prev"]
    if t_margin_tag:
        t_ws.range("F{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "mkt_margin_prev"]
        t_ws.range("H{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_margin_prev"]
    else:
        t_ws.range("F{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "mkt_val_prev"]
        t_ws.range("H{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_val_prev"]
    t_ws.range("I{}".format(t_s)).value = t_ws.range("G{}".format(t_s)).value
    t_ws.range("J{}".format(t_s)).value = t_ws.range("H{}".format(t_s)).value
    t_ws.range("K{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "pos_prop_prev"] / t_pos_prop_scale
    return 0


def update_r07_this_date(t_cid, t_cid_pos, t_ws, t_s, t_src_df, t_margin_tag, t_pos_prop_scale):
    t_ws.range("R{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "qty_this"]
    t_ws.range("S{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "settle_this"]
    t_ws.range("U{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_this"]
    if t_margin_tag:
        t_ws.range("T{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "mkt_margin_this"]
        t_ws.range("V{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_margin_this"]
    else:
        t_ws.range("T{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "mkt_val_this"]
        t_ws.range("V{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "cost_val_this"]
    t_ws.range("W{}".format(t_s)).value = t_ws.range("U{}".format(t_s)).value
    t_ws.range("X{}".format(t_s)).value = t_ws.range("V{}".format(t_s)).value
    t_ws.range("Y{}".format(t_s)).value = t_src_df.at[(t_cid, t_cid_pos), "pos_prop_this"] / t_pos_prop_scale
    return 0


def update_r07_trades(t_cid, t_cid_pos, t_traded_stats, t_ws, t_s, t_contract_multiplier, t_margin_rate):
    if t_cid_pos > 0:
        if t_traded_stats[(t_cid, t_cid_pos)]["open"] is None:
            t_ws.range("L{}:N{}".format(t_s, t_s)).value = 0
        else:
            df = t_traded_stats[(t_cid, t_cid_pos)]["open"]
            qty_sum = df["成交量"].sum()
            amt_sum = np.sum(df["成交量"] * df["成交均价"]) * t_contract_multiplier
            t_ws.range("L{}".format(t_s)).value = qty_sum
            t_ws.range("M{}".format(t_s)).value = amt_sum / qty_sum / t_contract_multiplier
            t_ws.range("N{}".format(t_s)).value = amt_sum * t_margin_rate

        if t_traded_stats[(t_cid, t_cid_pos)]["close"] is None:
            t_ws.range("O{}:Q{}".format(t_s, t_s)).value = 0
        else:
            df = t_traded_stats[(t_cid, t_cid_pos)]["close"]
            qty_sum = df["成交量"].sum()
            amt_sum = np.sum(df["成交量"] * df["成交均价"]) * t_contract_multiplier
            t_ws.range("O{}".format(t_s)).value = qty_sum
            t_ws.range("P{}".format(t_s)).value = amt_sum / qty_sum / t_contract_multiplier
            t_ws.range("Q{}".format(t_s)).value = amt_sum * t_margin_rate

    if t_cid_pos < 0:
        if t_traded_stats[(t_cid, t_cid_pos)]["close"] is None:
            t_ws.range("L{}:N{}".format(t_s, t_s)).value = 0
        else:
            df = t_traded_stats[(t_cid, t_cid_pos)]["close"]
            qty_sum = df["成交量"].sum()
            amt_sum = np.sum(df["成交量"] * df["成交均价"]) * t_contract_multiplier
            t_ws.range("L{}".format(t_s)).value = qty_sum
            t_ws.range("M{}".format(t_s)).value = amt_sum / qty_sum / t_contract_multiplier
            t_ws.range("N{}".format(t_s)).value = amt_sum * t_margin_rate

        if t_traded_stats[(t_cid, t_cid_pos)]["open"] is None:
            t_ws.range("O{}:Q{}".format(t_s, t_s)).value = 0
        else:
            df = t_traded_stats[(t_cid, t_cid_pos)]["open"]
            qty_sum = df["成交量"].sum()
            amt_sum = np.sum(df["成交量"] * df["成交均价"]) * t_contract_multiplier
            t_ws.range("O{}".format(t_s)).value = qty_sum
            t_ws.range("P{}".format(t_s)).value = amt_sum / qty_sum / t_contract_multiplier
            t_ws.range("Q{}".format(t_s)).value = amt_sum * t_margin_rate
    return 0


def get_premium(t_report_date: str, t_premium_book_path: str) -> float:
    _sheet_name = t_report_date[0:4]
    _premium_book_df = pd.read_excel(t_premium_book_path, sheet_name=_sheet_name)
    _premium_book_df["trade_date"] = _premium_book_df["日期"].map(lambda z: z.strftime("%Y%m%d"))
    _premium_book_df = _premium_book_df.set_index("trade_date")
    return _premium_book_df.at[t_report_date, "期末"]


def get_in_money(t_report_date: str, t_premium_book_path: str) -> float:
    _sheet_name = t_report_date[0:4]
    _premium_book_df = pd.read_excel(t_premium_book_path, sheet_name=_sheet_name)
    _premium_book_df["trade_date"] = _premium_book_df["日期"].map(lambda z: z.strftime("%Y%m%d"))
    _premium_book_df = _premium_book_df.set_index("trade_date")
    return _premium_book_df.at[t_report_date, "上账"]


def get_out_money(t_report_date: str, t_premium_book_path: str) -> float:
    _sheet_name = t_report_date[0:4]
    _premium_book_df = pd.read_excel(t_premium_book_path, sheet_name=_sheet_name)
    _premium_book_df["trade_date"] = _premium_book_df["日期"].map(lambda z: z.strftime("%Y%m%d"))
    _premium_book_df = _premium_book_df.set_index("trade_date")
    return _premium_book_df.at[t_report_date, "下账"]


def get_instrument_trailing_return_quantile(t_wind_code: str, t_report_date: str, t_major_return_dir: str,
                                            t_percentile: int = 5, t_trailing_window: int = 500, t_return_scale: float = 100):
    """

    :param t_wind_code: instrument_id in Wind format, such as "CU.SHF", "A.DCE", "MA.CZC"
    :param t_report_date: trailing window before this date (included)
    :param t_major_return_dir: directory where major return are saved
    :param t_percentile: integer between [0, 100], no greater than 50 is suggested
    :param t_trailing_window: how long to lookup
    :param t_return_scale：
    :return:
    """
    _major_return_file = "major_return.{}.close.csv.gz".format(t_wind_code)
    _major_return_path = os.path.join(t_major_return_dir, _major_return_file)
    _major_return_df = pd.read_csv(_major_return_path, dtype={"trade_date": str}).set_index("trade_date")
    _major_return_df = _major_return_df.loc[_major_return_df.index <= t_report_date].tail(t_trailing_window)
    q_l = np.percentile(_major_return_df["major_return"], q=t_percentile) / t_return_scale
    q_h = np.percentile(_major_return_df["major_return"], q=100 - t_percentile) / t_return_scale
    return q_l, q_h
