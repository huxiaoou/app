from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "risk_control"
start_row_num = 15
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- calendar
calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
prev_date = calendar.get_next_date(t_this_date=report_date, t_shift=-1)

# --- load premium
premium_tot = get_premium(t_report_date=report_date, t_premium_book_path=PREMIUM_BOOK_PATH)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load position data
this_pos_sum_file = "position.summary.{}.csv".format(report_date)
this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], this_pos_sum_file)
this_pos_sum_df = pd.read_csv(this_pos_sum_path, header=0)
if len(this_pos_sum_df) <= 0:
    print("No position info for {}".format(report_date))

# --- update instrument q05 q95 and VaR
this_pos_sum_by_instru_path = this_pos_sum_path.replace("position.summary", "position_by_instru.summary")
if os.path.exists(this_pos_sum_by_instru_path):
    this_pos_sum_by_instru_df = pd.read_csv(this_pos_sum_by_instru_path, header=0)
    this_pos_sum_by_instru_df["windCode"] = this_pos_sum_by_instru_df["instrument"].map(instrument_info.get_windCode)
    this_pos_sum_by_instru_df["q_l"], this_pos_sum_by_instru_df["q_h"] = zip(*this_pos_sum_by_instru_df["windCode"].map(
        lambda z: get_instrument_trailing_return_quantile(z, report_date, MAJOR_RETURN_DIR, 5, 500, 100)))
    this_pos_sum_by_instru_df["VaR"] = this_pos_sum_by_instru_df[["signed_mkt_val", "q_l", "q_h"]].apply(
        lambda z: z["signed_mkt_val"] * z["q_l"] if z["signed_mkt_val"] >= 0 else z["signed_mkt_val"] * z["q_h"],
        axis=1
    )
    report_date_VaR = this_pos_sum_by_instru_df["VaR"].abs().sum()
    report_date_VaR_true: tuple = cal_VaR(
        t_report_date=report_date,
        t_wgt_srs=this_pos_sum_by_instru_df.set_index("windCode")["signed_mkt_val"],
        t_major_return_dir=MAJOR_RETURN_DIR,
        t_percentile=5,
        t_trailing_window=500,
        t_return_scale=100
    )
else:
    report_date_VaR = 0
    report_date_VaR_true: tuple = 0, 0

# --- load margin data
this_margin_file = "margin.{}.csv".format(report_date)
this_margin_path = os.path.join(INTERMEDIARY_DIR, "margin", report_date[0:4], this_margin_file)
this_margin_df = pd.read_csv(this_margin_path).sort_values(by="mkt_margin", ascending=False)
if len(this_margin_df) > 0:
    max_margin_instru = this_margin_df["instrument"].iloc[0]
    max_margin_instru_amt = this_margin_df["mkt_margin"].iloc[0]
    max_margin_instru_ratio = this_margin_df["mkt_margin_ratio"].iloc[0]
else:
    max_margin_instru = ""
    max_margin_instru_amt = 0
    max_margin_instru_ratio = 0

# --- load summary data
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df = pd.read_csv(summary_stats_path, dtype={"trade_date": str}).set_index("trade_date")
mkt_val_tot = summary_stats_df.at[report_date, "mkt_val"]
mkt_val_by_instru_sum = summary_stats_df.at[report_date, "mkt_val_by_instru_sum"]
mkt_val_by_instru_max = summary_stats_df.at[report_date, "mkt_val_by_instru_max"]
mkt_val_net = summary_stats_df.at[report_date, "mkt_val_net"]
mkt_val_lng = summary_stats_df.at[report_date, "mkt_val_lng"]
mkt_val_srt = summary_stats_df.at[report_date, "mkt_val_srt"]
cost_val_tot = summary_stats_df.at[report_date, "cost_val"]
mkt_margin = summary_stats_df.at[report_date, "mkt_margin"]
pnl_tot = summary_stats_df.at[report_date, "tot_pnl"]
pnl_since_this_year = summary_stats_df.at[report_date, "tot_pnl"] - summary_stats_df.at[BASE_YEAR_DATE, "tot_pnl"]
q05 = summary_stats_df.at[prev_date, "q05"]
q95 = summary_stats_df.at[prev_date, "q95"]

# --- load nav data
nav_path = os.path.join(INTERMEDIARY_DIR, nav_file)
nav_df = pd.read_excel(nav_path)
nav_df["trade_date"] = nav_df["日期"].map(lambda z: z.strftime("%Y-%m-%d"))
nav_df["daily_premium"] = nav_df["入金"].cumsum() - nav_df["出金"].cumsum()
filter_this_year = (nav_df["trade_date"] > BASE_YEAR_DATE) & (nav_df["trade_date"] <= report_date)
daily_premium_aver = nav_df.loc[filter_this_year, "daily_premium"].mean()

# --- load settlement info
aux_file = "settle_info.{}.csv".format(report_date)
aux_path = os.path.join(INPUT_DIR, report_date[0:4], report_date, aux_file)
aux_df = pd.read_csv(aux_path)
aux_df["cid"] = aux_df["wind_code"].map(convert_wind_code_to_cid)
aux_df = aux_df.set_index("cid")

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]

# --- update template
ws.range("C1").value = expand_date_format(report_date)
s = start_row_num
qty_tot = 0
for ir in range(len(this_pos_sum_df)):
    cid = this_pos_sum_df.at[ir, "cid"]
    cid_pos = this_pos_sum_df.at[ir, "position"]
    instrument_id = parse_instrument_id(cid)
    if instrument_id in EXCEPTION_UNIVERSE:
        continue

    instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
    cid_chs = cid.replace(instrument_id, instrument_id_chs)
    cid_name = "{}({})".format(cid_chs, "多" if cid_pos > 0 else "空")
    contract_multiplier = instrument_info.get_multiplier(instrument_id)
    market = instrument_info.get_market_chs(instrument_id)

    qty = this_pos_sum_df.at[ir, "qty"]
    cost_prc = this_pos_sum_df.at[ir, "cost"]
    settle_prc = this_pos_sum_df.at[ir, "settle"]
    cost_val = this_pos_sum_df.at[ir, "cost_val"]
    mkt_val = this_pos_sum_df.at[ir, "mkt_val"]
    pos_prop = qty / aux_df.at[cid, "oi"]

    ws.range("B{}".format(s)).value = cid_name
    ws.range("C{}".format(s)).value = cid
    ws.range("D{}".format(s)).value = qty
    ws.range("E{}".format(s)).value = settle_prc
    ws.range("F{}".format(s)).value = mkt_val
    ws.range("G{}".format(s)).value = cost_prc
    ws.range("H{}".format(s)).value = cost_val
    ws.range("I{}".format(s)).value = (mkt_val / cost_val - 1) * cid_pos
    ws.range("J{}".format(s)).value = pos_prop
    ws.range("K{}".format(s)).value = mkt_val / mkt_val_tot

    qty_tot += qty
    s += 1
    ws.api.Rows(s).Insert()

# 小计
s += 2
ws.range("D{}".format(s)).value = qty_tot  # sum of quantity
ws.range("F{}".format(s)).value = mkt_val_tot  # sum of market value
ws.range("H{}".format(s)).value = cost_val_tot  # sum of cost value
ws.range("K{}".format(s)).value = 1 if mkt_val_tot > 0 else 0  # total proportion

# risk control indicator
# 方向性总敞口
s += 4
ws.range("F{}".format(s)).value = mkt_val_by_instru_sum / WAN_YUAN

# 市场风险资本准备占用
s += 1
scale_coe = 0.1
cal_coe = 0.2
ws.range("F{}".format(s)).value = mkt_val_tot * scale_coe * cal_coe / WAN_YUAN

# 损失预警限额：今年以来组合盈亏
s += 1
ws.range("F{}".format(s)).value = pnl_since_this_year / WAN_YUAN

# 单一标的方向性总敞口
s += 1
ws.range("F{}".format(s)).value = mkt_val_by_instru_max / WAN_YUAN

# 风险价值VAR值（市场风险整体）
s += 1
ws.range("F{}".format(s)).value = report_date_VaR / WAN_YUAN

# 业务规模
s += 1
ws.range("F{}".format(s)).value = premium_tot / WAN_YUAN

# 总保证金占比
s += 1
ws.range("F{}".format(s)).value = mkt_margin / (premium_tot + pnl_tot)

# 最大保证金品种-比例
s += 1
ws.range("F{}".format(s)).value = max_margin_instru_ratio / 100

# # ----------------- obsolete -----------------
# # 投资规模
# s += 1
# ws.range("B{}".format(s)).value = mkt_val_net / WAN_YUAN
#
# # 多头合约市值
# s += 1
# ws.range("B{}".format(s)).value = mkt_val_lng / WAN_YUAN
#
# # 空头合约市值
# s += 1
# ws.range("B{}".format(s)).value = mkt_val_srt / WAN_YUAN
#
# # 多空比
# s += 1
# ws.range("B{}".format(s)).value = mkt_val_lng / mkt_val_srt
#
# # 组合盈亏
# s += 1
# ws.range("B{}".format(s)).value = pnl_tot / WAN_YUAN
#
# # 往年已实现盈亏
# s += 1
# ws.range("B{}".format(s)).value = pnl_base_realize / WAN_YUAN
#
# # 杠杆系数
# s += 1
# ws.range("B{}".format(s)).value = mkt_val_net / (premium_tot + pnl_tot)
#
# # 日均业务规模
# s += 1
# ws.range("B{}".format(s)).value = daily_premium_aver / WAN_YUAN
#
# # 组合盈亏比例
# s += 1
# ws.range("B{}".format(s)).value = pnl_tot / daily_premium_aver
#
# # 总保证金
# s += 1
# ws.range("B{}".format(s)).value = mkt_margin / WAN_YUAN
#
# # 资金余额
# s += 1
# ws.range("B{}".format(s)).value = (premium_tot + pnl_tot - mkt_margin) / WAN_YUAN
#
# # 最大保证金品种
# s += 1
# ws.range("B{}".format(s)).value = max_margin_instru.upper() + "-" + CHS_NAME_MAPPER.get(max_margin_instru)
#
# # 最大保证金品种-规模
# s += 1
# ws.range("B{}".format(s)).value = max_margin_instru_amt / WAN_YUAN
#
# # VaR
# # 临界收益率
# s += 2
# ws.range("B{}".format(s)).value = q05 / 100 if mkt_val_net > 0 else q95 / 100
# # 对应亏损
# s += 1
# ws.range("B{}".format(s)).value = np.abs((q05 if mkt_val_net > 0 else q95) / 100 * mkt_val_net / WAN_YUAN)

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
