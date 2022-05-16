from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "traded_order"
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
template_file = TEMPLATES_FILE_LIST[report_name]

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load source data
src_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
src_path = os.path.join(save_dir, src_file)
if not os.path.exists(src_path):
    print("No trades need to be aggregated for {}".format(report_date))
    sys.exit()
src_df = pd.read_excel(src_path, header=2, sheet_name="大宗商品", dtype={"资金帐号": str})
src_df = src_df.dropna(axis=0, how="any")
src_df["成交数量"] = src_df["成交数量"].astype(int)

# --- aggregate raw data
agg_data_list = []
for gid_grp, gid_df in src_df.groupby(by=["资金帐号", "证券代码", "证券名称", "买卖标识"]):
    account_id, contract_id, contract_name, buy_sell_id = gid_grp
    amt_agg = gid_df["成交金额"].sum()
    qty_agg = gid_df["成交数量"].sum()
    instrument_id = parse_instrument_id(t_contract_id=contract_id)
    contract_multiplier = instrument_info.get_multiplier(t_instrument_id=instrument_id)
    aver_price = amt_agg / qty_agg / contract_multiplier
    agg_data_list.append({
        "account_id": account_id,
        "contract_id": contract_id,
        "contract_name": contract_name,
        "buy_sell_id": buy_sell_id,
        "qty_agg": qty_agg,
        "amt_agg": amt_agg,
        "aver_price": aver_price,
    })

# --- load report template
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]

# --- update template
start_row_num = 4
ws.range("G2").value = expand_date_format(report_date)
s = start_row_num
for ir, agg_data in zip(range(len(agg_data_list)), agg_data_list):
    ws.range("A{}".format(s)).value = agg_data["account_id"]
    ws.range("B{}".format(s)).value = agg_data["contract_id"]
    ws.range("C{}".format(s)).value = agg_data["contract_name"]
    ws.range("D{}".format(s)).value = agg_data["buy_sell_id"]
    ws.range("E{}".format(s)).value = agg_data["qty_agg"]
    ws.range("F{}".format(s)).value = agg_data["amt_agg"]
    ws.range("G{}".format(s)).value = agg_data["aver_price"]

    s += 1
    ws.api.Rows(s).Insert()

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + ".agg" + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
# wb.api.PrintOut()
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
