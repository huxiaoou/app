from configure import *
from WindPy import *
from tools_funs import *
from skyrim.whiterun import CCalendar

report_date = sys.argv[1]
calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
prev_date = calendar.get_next_date(report_date, t_shift=-1)

contract_set = set()

# update from position
for download_date in [prev_date, report_date]:
    pos_file = "position.{}.csv".format(download_date)
    pos_path = os.path.join(INPUT_DIR, download_date[0:4], download_date, pos_file)
    if not os.path.exists(pos_path):
        print("There is not any position info available for {}".format(download_date))
    else:
        pos_df = pd.read_csv(pos_path, encoding="gb18030")
        pos_df["wind_code"] = pos_df.apply(
            lambda z: convert_contract_format(z["代码"], z["市场代码"], EXCHANGE_ID_ENG), axis=1)
        contract_set = contract_set.union(set(pos_df["wind_code"]))

# update from trades in this date
# some intra-day trades may not exist in either prev date or this date
traded_file = "traded.{}.csv".format(report_date)
traded_path = os.path.join(INPUT_DIR, report_date[0:4], report_date, traded_file)
if not os.path.exists(traded_path):
    print("There is not any trades info available for {}".format(download_date))
else:
    traded_df = pd.read_csv(traded_path, encoding="gb18030")
    traded_df["wind_code"] = traded_df.apply(
        lambda z: convert_contract_format(z["合约代码"], z["交易所名称"], EXCHANGE_ID_CHS), axis=1)
    contract_set = contract_set.union(set(traded_df["wind_code"]))

# download
if len(contract_set) == 0:
    aux_df = pd.DataFrame(columns=["settle", "oi", "margin_rate"])
else:
    w.start()
    contract_list = list(contract_set)
    data_settle = w.wsd(contract_list, "settle", report_date, report_date, "")
    data_oi = w.wsd(contract_list, "oi", report_date, report_date, "")
    data_margin_rate = w.wsd(contract_list, "margin", report_date, report_date, "")
    aux_df = pd.DataFrame(
        {
            "settle": pd.Series(data=data_settle.Data[0], index=contract_list),
            "oi": pd.Series(data=data_oi.Data[0], index=contract_list),
            "margin_rate": pd.Series(data=data_margin_rate.Data[0], index=contract_list),
        }
    )
    aux_df["margin_rate"] = aux_df["margin_rate"] / MARGIN_RATE_SCALE
    aux_df = aux_df.sort_index(ascending=True)
    print("| {1} | {0} | aux data downloaded |\n".format(report_date, dt.datetime.now()))

save_dir = os.path.join(INPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)
save_file = "settle_info.{}.csv".format(report_date)
save_path = os.path.join(save_dir, save_file)
aux_df.to_csv(save_path, index_label="wind_code", float_format="%.2f")

print(aux_df)

# download CCFI.WI
idx_label = "CCFI.WI"
idx_data = w.wsd(idx_label, "open,high,low,close,pct_chg", prev_date, prev_date, "")
idx_df = pd.DataFrame(idx_data.Data, index=idx_data.Fields, columns=[prev_date]).T
idx_file = "market_index.{}.csv".format(prev_date)
save_dir = os.path.join(INPUT_DIR, prev_date[0:4], prev_date)
idx_path = os.path.join(save_dir, idx_file)
idx_df.to_csv(idx_path, index_label="trade_date", float_format="%.6f")
print(idx_df)
