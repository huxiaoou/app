from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "traded_order"
start_row_num = 4
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load source data
input_df, traded_df = load_input_and_traded_data(t_report_date=report_date, t_input_dir=INPUT_DIR)
if input_df is None:
    print("this script will terminated at once")
    sys.exit()

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]

# --- update template
ws.range("G2").value = expand_date_format(report_date)
s = start_row_num
for ir in range(len(traded_df)):
    cid = traded_df.at[ir, "合约代码"]
    instrument_id = parse_instrument_id(cid)
    if instrument_id in EXCEPTION_UNIVERSE:
        continue

    instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
    cid_chs = cid.replace(instrument_id, instrument_id_chs)
    contract_multiplier = instrument_info.get_multiplier(instrument_id)

    buy_sell_flag = traded_df.at[ir, "买卖方向"] + traded_df.at[ir, "多空方向"]
    traded_qty = traded_df.at[ir, "成交量"]
    traded_price = traded_df.at[ir, "成交均价"]
    traded_amt = traded_price * contract_multiplier * traded_qty

    ws.range("A{}".format(s)).value = ACCOUNT
    ws.range("B{}".format(s)).value = cid
    ws.range("C{}".format(s)).value = cid_chs
    ws.range("D{}".format(s)).value = buy_sell_flag
    ws.range("E{}".format(s)).value = traded_qty
    ws.range("F{}".format(s)).value = traded_amt
    ws.range("G{}".format(s)).value = traded_price

    s += 1
    ws.api.Rows(s).Insert()

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
sleep(3)
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
