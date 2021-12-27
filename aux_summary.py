from setup import *
from configure import BGN_DATE
from skyrim.whiterun import CCalendar

report_date = sys.argv[1]

calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
next_date = calendar.get_next_date(t_this_date=report_date, t_shift=1)

# --- load
calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
var_bgn_date = calendar.get_next_date(t_this_date=BGN_DATE, t_shift=-504)
idx_dfs_list = []
for trade_date in calendar.get_iter_list(t_bgn_date=var_bgn_date, t_stp_date=report_date, t_ascending=True):
    idx_file = "market_index.{}.csv".format(trade_date)
    idx_path = os.path.join(INPUT_DIR, trade_date[0:4], trade_date, idx_file)
    idx_df = pd.read_csv(idx_path, dtype={"trade_date": str})
    idx_dfs_list.append(idx_df)
idx_md_df = pd.concat(idx_dfs_list, ignore_index=True, axis=0)
idx_md_df["q05"] = idx_md_df["PCT_CHG"].rolling(window=504).apply(lambda z: np.percentile(z, q=5))
idx_md_df["q95"] = idx_md_df["PCT_CHG"].rolling(window=504).apply(lambda z: np.percentile(z, q=95))
idx_md_df = idx_md_df.set_index("trade_date")

summary_stats = []
realized_pnl_cumsum = 0
for trade_date in calendar.get_iter_list(t_bgn_date=BGN_DATE, t_stp_date=next_date, t_ascending=True):
    this_pos_sum_file = "position.summary.{}.csv".format(trade_date)
    this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", trade_date[0:4], this_pos_sum_file)
    this_pos_sum_df = pd.read_csv(this_pos_sum_path, header=0)

    # save realized pnl
    this_realized_file = "realized.pnl.{}.csv".format(trade_date)
    this_realized_path = os.path.join(INTERMEDIARY_DIR, "realized_pnl", trade_date[0:4], this_realized_file)
    this_realized_df = pd.read_csv(this_realized_path, header=0)

    unrealized_pnl = 0
    cost_val = 0
    mkt_val = 0
    mkt_val_net = 0
    mkt_val_lng = 0
    mkt_val_srt = 0
    cost_margin = 0
    mkt_margin = 0
    if len(this_pos_sum_df) > 0:
        unrealized_pnl = this_pos_sum_df["unrealized_pnl"].sum()
        cost_val = this_pos_sum_df["cost_val"].sum()
        mkt_val = this_pos_sum_df["mkt_val"].sum()
        mkt_val_net = (this_pos_sum_df["position"] * this_pos_sum_df["mkt_val"]).sum()
        mkt_val_lng = this_pos_sum_df.apply(lambda z: z["mkt_val"] if z["position"] > 0 else 0, axis=1).sum()
        mkt_val_srt = this_pos_sum_df.apply(lambda z: z["mkt_val"] if z["position"] < 0 else 0, axis=1).sum()
        cost_margin = this_pos_sum_df["cost_margin"].sum()
        mkt_margin = this_pos_sum_df["mkt_margin"].sum()

    realized_pnl = 0
    if len(this_realized_df) > 0:
        realized_pnl = this_realized_df["realized_pnl"].sum()

    realized_pnl_cumsum += realized_pnl
    summary_stats.append({
        "trade_date": trade_date,
        "realized_pnl": realized_pnl,
        "realized_pnl_cumsum": realized_pnl_cumsum,
        "unrealized_pnl": unrealized_pnl,
        "tot_pnl": realized_pnl_cumsum + unrealized_pnl,
        "cost_val": cost_val,
        "mkt_val": mkt_val,
        "mkt_val_net": mkt_val_net,
        "mkt_val_lng": mkt_val_lng,
        "mkt_val_srt": mkt_val_srt,
        "cost_margin": cost_margin,
        "mkt_margin": mkt_margin,
        "q05": idx_md_df.at[trade_date, "q05"] if trade_date < report_date else None,
        "q95": idx_md_df.at[trade_date, "q95"] if trade_date < report_date else None,
    })

summary_stats_df = pd.DataFrame(summary_stats)
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df.to_csv(summary_stats_path, index=False, float_format="%.6f")
print(summary_stats_df.tail(10))
