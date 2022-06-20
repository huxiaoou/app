from tools_funs import *
from tools_class import *
from configure import *

report_date = sys.argv[1]
report_name = "pnl_summary"
start_row_num = 4
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load position data
this_pos_sum_file = "position.summary.{}.csv".format(report_date)
this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], this_pos_sum_file)
this_pos_sum_df = pd.read_csv(this_pos_sum_path, header=0)
if len(this_pos_sum_df) <= 0:
    qty_sum = 0
    print("No position info for {}".format(report_date))
else:
    qty_sum = this_pos_sum_df["qty"].sum()

# --- load pnl data
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df = pd.read_csv(summary_stats_path, dtype={"trade_date": str}).set_index("trade_date")

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]

# --- update template
ws.range("A2").value = "日期：" + expand_date_format(report_date)
for s in range(start_row_num, start_row_num + 2):
    ws.range("B{}".format(s)).value = qty_sum
    ws.range("C{}".format(s)).value = summary_stats_df.at[report_date, "mkt_val"] / WAN_YUAN

    realized_pnl_since_base = (summary_stats_df.at[report_date, "realized_pnl_cumsum"] - summary_stats_df.at[BASE_YEAR_DATE, "realized_pnl_cumsum"]) / WAN_YUAN
    unrealized_pnl_since_base = (summary_stats_df.at[report_date, "unrealized_pnl"] - summary_stats_df.at[BASE_YEAR_DATE, "unrealized_pnl"]) / WAN_YUAN
    tot_pnl_since_base = (summary_stats_df.at[report_date, "tot_pnl"] - summary_stats_df.at[BASE_YEAR_DATE, "tot_pnl"]) / WAN_YUAN

    ws.range("D{}".format(s)).value = unrealized_pnl_since_base
    ws.range("E{}".format(s)).value = realized_pnl_since_base
    ws.range("F{}".format(s)).value = tot_pnl_since_base

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
sleep(3)
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
