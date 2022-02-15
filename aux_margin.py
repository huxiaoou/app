from setup import *
from configure import PREMIUM_BOOK_PATH
from tools_funs import get_premium
from skyrim.whiterun import parse_instrument_from_contract
from skyrim.winterhold import check_and_mkdir

report_date = sys.argv[1]

# --- load premium
premium_tot = get_premium(t_report_date=report_date, t_premium_book_path=PREMIUM_BOOK_PATH)

# --- load pnl data
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df = pd.read_csv(summary_stats_path, dtype={"trade_date": str}).set_index("trade_date")
pnl_tot = summary_stats_df.at[report_date, "tot_pnl"]

# load position summary
report_pos_sum_file = "position.summary.{}.csv".format(report_date)
report_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], report_pos_sum_file)
report_pos_sum_df = pd.read_csv(report_pos_sum_path, header=0)

if len(report_pos_sum_df) == 0:
    report_margin_df = pd.DataFrame(columns=["instrument", "qty", "cost_margin", "mkt_margin", "cost_margin_ratio", "mkt_margin_ratio"])
else:
    report_pos_sum_df["instrument"] = report_pos_sum_df["cid"].map(parse_instrument_from_contract)
    report_margin_df = pd.pivot_table(data=report_pos_sum_df, index="instrument", values=["qty", "cost_margin", "mkt_margin"], aggfunc=sum)
    report_margin_df = report_margin_df[["qty", "cost_margin", "mkt_margin"]]
    report_margin_df["cost_margin_ratio"] = report_margin_df["cost_margin"] / (premium_tot + pnl_tot) * 100
    report_margin_df["mkt_margin_ratio"] = report_margin_df["mkt_margin"] / (premium_tot + pnl_tot) * 100
    report_margin_df = report_margin_df.sort_values(by=["mkt_margin"], ascending=False)

report_margin_file = "margin.{}.csv".format(report_date)
check_and_mkdir(os.path.join(INTERMEDIARY_DIR, "margin", report_date[0:4]))
report_margin_path = os.path.join(INTERMEDIARY_DIR, "margin", report_date[0:4], report_margin_file)
report_margin_df.to_csv(report_margin_path, index_label="instrument", float_format="%.4f")
print("| {1} | {0} | intermediary data | margin | calculated |".format(report_date, dt.datetime.now()))
