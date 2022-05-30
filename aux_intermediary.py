from tools_class import *
from tools_funs import *
from configure import EXCEPTION_UNIVERSE, POS_PROP_SCALE
from skyrim.whiterun import CCalendar

calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
report_date = sys.argv[1]
prev_date = calendar.get_next_date(report_date, t_shift=-1)

# --- load prev position
prev_pos_sum_file = "position.summary.{}.csv".format(prev_date)
prev_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", prev_date[0:4], prev_pos_sum_file)
prev_pos_sum_df = pd.read_csv(prev_pos_sum_path)
prev_pos_sum_df = prev_pos_sum_df.set_index(["cid", "position"])
prev_pos_sum = prev_pos_sum_df.to_dict(orient='index')

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load settlement info
aux_file = "settle_info.{}.csv".format(report_date)
aux_path = os.path.join(INPUT_DIR, report_date[0:4], report_date, aux_file)
aux_df = pd.read_csv(aux_path, header=0)
aux_df["cid"] = aux_df["wind_code"].map(convert_wind_code_to_cid)
aux_df = aux_df.set_index("cid")

# --- load source data
input_df, traded_df = load_input_and_traded_data(t_report_date=report_date, t_input_dir=INPUT_DIR)  # type: (pd.DataFrame, pd.DataFrame)

this_sum = {}
# --- calculate position summary
# --- --- Part I: in today's trades
if traded_df is not None:
    traded_stats = group_traded_data(t_traded_df=traded_df, t_exception_universe=EXCEPTION_UNIVERSE)
    for (cid, cid_pos), operation_dfs in traded_stats.items():
        instrument_id = parse_instrument_id(cid)
        contract_multiplier = instrument_info.get_multiplier(instrument_id)

        qty_prev = 0
        amt_prev = 0
        if (cid, cid_pos) in prev_pos_sum:
            qty_prev = prev_pos_sum[(cid, cid_pos)]["qty"]
            prc_prev = prev_pos_sum[(cid, cid_pos)]["cost"]
            amt_prev = qty_prev * prc_prev

        qty_open = 0
        amt_open = 0
        if operation_dfs["open"] is not None:
            qty_open = operation_dfs["open"]["成交量"].sum()
            amt_open = np.sum(operation_dfs["open"]["成交量"] * operation_dfs["open"]["成交均价"])

        cost_this = (amt_prev + amt_open) / (qty_prev + qty_open)

        qty_close = 0
        realized_pnl_this = 0
        realized_tag = False
        if operation_dfs["close"] is not None:
            qty_close = operation_dfs["close"]["成交量"].sum()
            realized_pnl_this = np.sum(operation_dfs["close"]["成交量"] * (operation_dfs["close"]["成交均价"] - cost_this) * contract_multiplier * cid_pos)
            realized_tag = True

        qty_this = qty_prev + qty_open - qty_close
        settle_this = 0
        margin_rate = 0
        pos_prop = 0
        if qty_this > 0:
            settle_this = aux_df.at[cid, "settle"]
            margin_rate = aux_df.at[cid, "margin_rate"]
            pos_prop = qty_this / aux_df.at[cid, "oi"] * POS_PROP_SCALE
        unrealized_pnl_this = qty_this * (settle_this - cost_this) * contract_multiplier * cid_pos

        cost_val = cost_this * contract_multiplier * qty_this
        mkt_val = settle_this * contract_multiplier * qty_this
        cost_margin = cost_val * margin_rate
        mkt_margin = mkt_val * margin_rate

        this_sum[(cid, cid_pos)] = {
            "qty": qty_this,
            "cost": cost_this,
            "settle": settle_this,
            "realized_tag": realized_tag,
            "realized_pnl": realized_pnl_this,
            "unrealized_pnl": unrealized_pnl_this,
            "cost_val": cost_val,
            "mkt_val": mkt_val,
            "cost_margin": cost_margin,
            "mkt_margin": mkt_margin,
            "pos_prop": pos_prop,
        }

# --- --- Part II: in prev date not in today
for (cid, cid_pos), cid_pos_df in prev_pos_sum.items():
    if (cid, cid_pos) not in this_sum:
        instrument_id = parse_instrument_id(cid)
        contract_multiplier = instrument_info.get_multiplier(instrument_id)
        settle_this = aux_df.at[cid, "settle"]
        margin_rate = aux_df.at[cid, "margin_rate"]
        qty_this = prev_pos_sum[(cid, cid_pos)]["qty"]
        pos_prop = qty_this / aux_df.at[cid, "oi"] * POS_PROP_SCALE
        cost_this = prev_pos_sum[(cid, cid_pos)]["cost"]
        unrealized_pnl_this = (settle_this - cost_this) * contract_multiplier * qty_this * cid_pos

        cost_val = cost_this * contract_multiplier * qty_this
        mkt_val = settle_this * contract_multiplier * qty_this
        cost_margin = cost_val * margin_rate
        mkt_margin = mkt_val * margin_rate

        this_sum[(cid, cid_pos)] = {
            "qty": qty_this,
            "cost": cost_this,
            "settle": settle_this,
            "realized_tag": False,
            "realized_pnl": 0,
            "unrealized_pnl": unrealized_pnl_this,
            "cost_val": cost_val,
            "mkt_val": mkt_val,
            "cost_margin": cost_margin,
            "mkt_margin": mkt_margin,
            "pos_prop": pos_prop,
        }

this_sum_df = pd.DataFrame.from_dict(this_sum, orient="index")
this_sum_df = this_sum_df.reset_index().rename(axis=1, mapper={"level_0": "cid", "level_1": "position"})

this_pos_sum_file = "position.summary.{}.csv".format(report_date)
this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], this_pos_sum_file)
this_realized_file = "realized.pnl.{}.csv".format(report_date)
this_realized_path = os.path.join(INTERMEDIARY_DIR, "realized_pnl", report_date[0:4], this_realized_file)
if len(this_sum_df) > 0:
    idx_pos = this_sum_df["qty"] > 0
    this_pos_sum_df = this_sum_df.loc[idx_pos].drop(axis=1, labels=["realized_tag", "realized_pnl"])  # type:pd.DataFrame
    idx_realized = this_sum_df["realized_tag"]
    this_realized_df = this_sum_df.loc[idx_realized, ["cid", "position", "realized_pnl"]]  # type:pd.DataFrame

else:
    this_pos_sum_df = pd.DataFrame(columns=["cid", "position", "qty", "cost", "settle", "unrealized_pnl", "cost_val", "mkt_val", "cost_margin", "mkt_margin", "pos_prop"])
    this_realized_df = pd.DataFrame(columns=["cid", "position", "realized_pnl"])

this_pos_sum_df.to_csv(this_pos_sum_path, index=False, float_format="%.6f")
this_realized_df.to_csv(this_realized_path, index=False, float_format="%.6f")

# --- position by instrument
# updated @ 2022-05-30
this_pos_sum_df["instrument"] = this_pos_sum_df["cid"].map(parse_instrument_id)
this_pos_sum_df["signed_mkt_val"] = this_pos_sum_df["position"] * this_pos_sum_df["mkt_val"]
this_pos_sum_df["signed_cost_val"] = this_pos_sum_df["position"] * this_pos_sum_df["cost_val"]

this_pos_sum_by_instru_df = pd.pivot_table(
    data=this_pos_sum_df,
    index="instrument",
    values=["signed_mkt_val", "signed_cost_val"],
    aggfunc=sum
)
this_pos_sum_by_instru_df = this_pos_sum_by_instru_df.sort_index(ascending=True)
this_pos_sum_by_instru_path = this_pos_sum_path.replace("position.summary", "position_by_instru.summary")
this_pos_sum_by_instru_df.to_csv(this_pos_sum_by_instru_path, index_label="instrument", float_format="%.6f")

print("| {1} | {0} | intermediary data | calculated |".format(report_date, dt.datetime.now()))
