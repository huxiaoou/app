from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "input_order_outside"
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
ws.range("I2").value = expand_date_format(report_date)
s = start_row_num
for ir in range(len(input_df)):
    cid = input_df.at[ir, "合约代码"]
    instrument_id = parse_instrument_id(cid)
    if instrument_id in EXCEPTION_UNIVERSE:
        continue

    instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
    cid_chs = cid.replace(instrument_id, instrument_id_chs)
    contract_multiplier = instrument_info.get_multiplier(instrument_id)

    buy_sell_flag = input_df.at[ir, "买卖方向"] + input_df.at[ir, "多空方向"]
    input_qty = input_df.at[ir, "委托量"]
    input_price = input_df.at[ir, "限价"]

    ws.range("A{}".format(s)).value = s - start_row_num + 1
    ws.range("B{}".format(s)).value = cid
    ws.range("C{}".format(s)).value = cid_chs
    ws.range("D{}".format(s)).value = buy_sell_flag
    ws.range("E{}".format(s)).value = input_price
    ws.range("F{}".format(s)).value = input_qty
    ws.range("I{}".format(s)).value = PERMISSION_CODE

    s += 1
    ws.api.Rows(s).Insert()

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
# wb.api.PrintOut()
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
