from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "traded_order_summary"
start_row_num = 4
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]
ws.range("A1").value = "日期：" + expand_date_format(report_date)

# --- load source data
input_df, traded_df = load_input_and_traded_data(t_report_date=report_date, t_input_dir=INPUT_DIR)
if traded_df is not None:
    traded_stats = group_traded_data(t_traded_df=traded_df, t_exception_universe=EXCEPTION_UNIVERSE)
    s = start_row_num
    qty_sum = 0
    amt_sum = 0
    for (cid, cid_pos), operation_dfs in traded_stats.items():
        instrument_id = parse_instrument_id(cid)
        if instrument_id in EXCEPTION_UNIVERSE:
            continue

        instrument_id = parse_instrument_id(cid)
        instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
        cid_chs = cid.replace(instrument_id, instrument_id_chs)
        contract_multiplier = instrument_info.get_multiplier(instrument_id)
        market = instrument_info.get_market_chs(instrument_id)

        for direction in ["open", "close"]:
            if operation_dfs[direction] is not None:
                df = operation_dfs[direction]
                if direction == "open":
                    cid_name = "{}({}开)".format(cid_chs, "买" if cid_pos > 0 else "卖")
                    flow_s = -1 if cid_pos > 0 else 1
                else:
                    cid_name = "{}({}平)".format(cid_chs, "卖" if cid_pos > 0 else "买")
                    flow_s = 1 if cid_pos > 0 else -1
                traded_qty = df["成交量"].sum()
                traded_amt = np.sum(df["成交量"] * df["成交均价"]) * contract_multiplier
                traded_prc = traded_amt / traded_qty / contract_multiplier

                ws.range("A{}".format(s)).value = "商品期货"
                ws.range("B{}".format(s)).value = cid
                ws.range("C{}".format(s)).value = cid_name
                ws.range("D{}".format(s)).value = traded_prc
                ws.range("E{}".format(s)).value = traded_qty
                ws.range("F{}".format(s)).value = traded_amt * flow_s
                ws.range("G{}".format(s)).value = market
                qty_sum += traded_qty
                amt_sum += traded_amt * flow_s
                s += 1
                ws.api.Rows(s).Insert()

    # 合计
    s += 2
    ws.range("E{}".format(s)).value = qty_sum
    ws.range("F{}".format(s)).value = amt_sum

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
