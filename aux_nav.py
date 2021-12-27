from setup import *
from tools_class import CNAV
from configure import nav_file, WAN_YUAN
from skyrim.whiterun import CCalendar

report_date = sys.argv[1]
calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
prev_date = calendar.get_next_date(report_date, t_shift=-1)

print("IMPORTANT : if {} is a in-money/out-share date, make sure to set the corresponding variable manually before run".format(report_date))
in_money = 0 * WAN_YUAN  # 入金
out_share = 0  # 转出份额

# load data
summary_stats_file = "summary.csv"
summary_stats_path = os.path.join(INTERMEDIARY_DIR, summary_stats_file)
summary_stats_df = pd.read_csv(summary_stats_path, dtype={"trade_date": str}).set_index("trade_date")
realized_pnl = summary_stats_df.at[report_date, "realized_pnl"]
unrealized_pnl = summary_stats_df.at[report_date, "unrealized_pnl"]

# load nav file
nav_path = os.path.join(INTERMEDIARY_DIR, nav_file)
wb = xw.Book(nav_path)
ws = wb.sheets["期货净值表"]

# set the first empty row idx = s
s = 2
while ws.range("A{}".format(s)).value is not None:
    s += 1

# check last date
last_date = ws.range("A{}".format(s - 1)).value.strftime("%Y%m%d")
if last_date != prev_date:
    if last_date == report_date:
        print("last date {} in nav table = report date {}. An overwrite operation will be applied to the nav table.".format(last_date, report_date))
        s -= 1
    else:
        print("Error! the last date {} in the excel table != report date {}".format(last_date, prev_date))
        wb.close()
        sys.exit()

ws.range("A{}".format(s)).value = report_date[0:4] + "-" + report_date[4:6] + "-" + report_date[6:8]
ws.range("B{}".format(s)).formula = "=F{}".format(s - 1)
ws.range("C{}".format(s)).value = realized_pnl
ws.range("D{}".format(s)).formula = "=D{0}+C{1}".format(s - 1, s)
ws.range("E{}".format(s)).value = unrealized_pnl
ws.range("F{}".format(s)).formula = "=B{1}-E{0}+E{1}+C{1}+G{1}-H{1}".format(s - 1, s)
ws.range("G{}".format(s)).value = in_money  # 入金
ws.range("H{}".format(s)).formula = "=K{1}*M{0}".format(s - 1, s)
ws.range("I{}".format(s)).formula = "=L{}".format(s - 1)
ws.range("J{}".format(s)).formula = "=G{1}/M{0}".format(s - 1, s)
ws.range("K{}".format(s)).value = out_share  # 份额减少
ws.range("L{}".format(s)).formula = "=I{0}+J{0}-K{0}".format(s)
ws.range("M{}".format(s)).formula = "=F{0}/L{0}".format(s)
ws.range("N{}".format(s)).formula = "=M{1}/M{0}-1".format(s - 1, s)

# insert
s += 1
ws.api.Rows(s).Insert()
print("| {} | {} | nav table updated |".format(dt.datetime.now(), report_date))

# save
wb.save()
wb.close()

# load nav
nav_df = pd.read_excel(nav_path)
nav_df["trade_date"] = nav_df["日期"].map(lambda z: z.strftime("%Y-%m-%d"))
nav_df["nav"] = nav_df["单位净值"]
nav_df = nav_df[["trade_date", "nav"]].set_index("trade_date")

# return-risk index
nav = CNAV(t_nav_srs=nav_df["nav"], t_annual_rf_rate=2.5, t_freq="D")
nav.cal_annual_return()
nav.cal_max_drawdown()
nav.cal_mdd_duration(t_calendar=calendar)
nav.cal_sharpe_ratio0()
nav.cal_sharpe_ratio1()
nav.cal_hold_period_return()
return_risk_index = nav.to_dict()
description = "年化收益={:.2f}%\n夏普比率={:.2f}\n最大回撤={:.2f}%".format(
    return_risk_index["annual_return"],
    return_risk_index["sharpe_ratio"],
    return_risk_index["max_drawdown"],
)

# --- plot
last_date = nav_df.index[-1]
for i in range(1, 3):
    next_date = calendar.get_next_date(t_this_date=last_date.replace("-", ""), t_shift=i)
    append_date = next_date[0:4] + "-" + next_date[4:6] + "-" + next_date[6:8]
    nav_df = nav_df.append(pd.Series(name=append_date, dtype=float))
y_max = nav_df["nav"].max()
y_min = nav_df["nav"].min()

n_ticks = len(nav_df)
fig0, ax0 = plt.subplots(figsize=(16, 9))
nav_df.plot(ax=ax0, lw=3.0)
xticks = np.arange(0, n_ticks, int(n_ticks / 7))
xticklabels = nav_df.index[xticks]
ax0.set_xticks(xticks)
ax0.set_xticklabels(xticklabels, fontdict=fd)
ax0.set_xlabel("")

yticks = np.arange(y_min * 0.95, y_max * 1.05, 0.02)
yticklabels = ["{:.2f}".format(_) for _ in yticks]
ax0.set_yticks(yticks)
ax0.set_yticklabels(yticklabels, fontdict=fd)
ax0.yaxis.tick_right()

ax0.set_ylim((y_min * 0.96, y_max * 1.04))
ax0.text(
    x=3, y=y_max * 1.04 * 0.950, s=description, fontdict={"size": 16, "weight": "heavy"},
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
)
ax0.get_legend().remove()
ax0.set_title("单位净值")
fig0_name = "组合净值.png"
fig0_path = os.path.join(INTERMEDIARY_DIR, fig0_name)
fig0.savefig(fig0_path, bbox_inches="tight")
plt.close(fig0)

print("| {} | {} | nav plotted |".format(dt.datetime.now(), report_date))
