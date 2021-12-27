from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "position_details"
start_row_num = 5
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load pnl data
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df = pd.read_csv(summary_stats_path, dtype={"trade_date": str}).set_index("trade_date")

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]
ws.range("A2").value = "统计日期：" + expand_date_format(report_date)

# --- load position data
this_pos_sum_file = "position.summary.{}.csv".format(report_date)
this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], this_pos_sum_file)
this_pos_sum_df = pd.read_csv(this_pos_sum_path, header=0)

s = start_row_num
if len(this_pos_sum_df) <= 0:
    print("No position info for {}".format(report_date))
else:
    qty_sum = 0
    cost_val_sum = 0
    mkt_val_sum = 0
    float_pnl_sum = 0
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
        float_pnl = (mkt_val - cost_val) * cid_pos

        ws.range("A{}".format(s)).value = cid_name
        ws.range("B{}".format(s)).value = cid
        ws.range("C{}".format(s)).value = qty
        ws.range("D{}".format(s)).value = cost_prc
        ws.range("E{}".format(s)).value = cost_val
        ws.range("F{}".format(s)).value = settle_prc
        ws.range("G{}".format(s)).value = mkt_val
        ws.range("H{}".format(s)).value = float_pnl
        ws.range("I{}".format(s)).value = (mkt_val / cost_val - 1) * cid_pos

        # sum
        qty_sum += qty
        cost_val_sum += cost_val
        mkt_val_sum += mkt_val
        float_pnl_sum += float_pnl

        # for next
        s += 1
        ws.api.Rows(s).Insert()

    # 合计
    s += 2
    ws.range("C{}".format(s)).value = qty_sum
    ws.range("E{}".format(s)).value = cost_val_sum
    ws.range("G{}".format(s)).value = mkt_val_sum
    ws.range("H{}".format(s)).value = float_pnl_sum

# compared to prev year
realized_pnl_since_base = (summary_stats_df.at[report_date, "realized_pnl_cumsum"] - summary_stats_df.at[BASE_YEAR_DATE, "realized_pnl_cumsum"]) / WAN_YUAN
unrealized_pnl_since_base = (summary_stats_df.at[report_date, "unrealized_pnl"] - summary_stats_df.at[BASE_YEAR_DATE, "unrealized_pnl"]) / WAN_YUAN
tot_pnl_since_base = (summary_stats_df.at[report_date, "tot_pnl"] - summary_stats_df.at[BASE_YEAR_DATE, "tot_pnl"]) / WAN_YUAN

pnl_sum_txt = "注：年初至今，实现盈利约{:.2f}万元，持仓盈亏{:.2f}万元，合计投资收益约{:.2f}万元。".format(
    np.round(realized_pnl_since_base, 2),
    np.round(unrealized_pnl_since_base, 2),
    np.round(tot_pnl_since_base, 2),
)
s += 1
ws.range("A{}".format(s)).value = pnl_sum_txt
print("按结算价计持仓本日浮动盈亏{:.2f}万元，累计盈亏{:.2f}万元。".format(
    np.round(unrealized_pnl_since_base, 2),
    np.round(tot_pnl_since_base, 2),
))

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
