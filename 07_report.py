from configure import *
from tools_funs import *
from tools_class import CInstrumentInfo
from skyrim.whiterun import CCalendar

report_date = sys.argv[1]
sub_type = sys.argv[2]

calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))
prev_date = calendar.get_next_date(report_date, t_shift=-1)
if sub_type == "no_margin":
    report_name = "report_no_margin"
    margin_tag = False
elif sub_type == "margin":
    report_name = "report_margin"
    margin_tag = True
else:
    print("table mode are not right, please check again.")
    sys.exit()

start_row_num = 54
save_dir = os.path.join(OUTPUT_DIR, report_date[0:4], report_date)
check_and_mkdir(save_dir)

# --- load instrument info
instrument_info = CInstrumentInfo(os.path.join(INSTRUMENT_INFO_DIR, "InstrumentInfo.xlsx"))

# --- load source data
input_df, traded_df = load_input_and_traded_data(t_report_date=report_date, t_input_dir=INPUT_DIR)
if traded_df is None:
    traded_stats = {}
    print("No traded info for {}".format(report_date))
else:
    traded_stats = group_traded_data(t_traded_df=traded_df, t_exception_universe=EXCEPTION_UNIVERSE)

# --- load settlement info
aux_file = "settle_info.{}.csv".format(report_date)
aux_path = os.path.join(INPUT_DIR, report_date[0:4], report_date, aux_file)
aux_df = pd.read_csv(aux_path)
aux_df["cid"] = aux_df["wind_code"].map(convert_wind_code_to_cid)
aux_df = aux_df.set_index("cid")

# --- load prev position data
prev_pos_sum_file = "position.summary.{}.csv".format(prev_date)
prev_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", prev_date[0:4], prev_pos_sum_file)
prev_pos_sum_df = pd.read_csv(prev_pos_sum_path, header=0)
prev_pos_sum_df = prev_pos_sum_df.set_index(["cid", "position"])
if len(prev_pos_sum_df) <= 0:
    print("No position info for {}".format(prev_date))

# --- load this position data
this_pos_sum_file = "position.summary.{}.csv".format(report_date)
this_pos_sum_path = os.path.join(INTERMEDIARY_DIR, "position_summary", report_date[0:4], this_pos_sum_file)
this_pos_sum_df = pd.read_csv(this_pos_sum_path, header=0)
this_pos_sum_df = this_pos_sum_df.set_index(["cid", "position"])
if len(this_pos_sum_df) <= 0:
    print("No position info for {}".format(report_date))

# --- load report template
template_file = TEMPLATES_FILE_LIST[report_name]
template_path = os.path.join(TEMPLATES_DIR, template_file)
wb = xw.Book(template_path)
ws = wb.sheets["大宗商品"]
ws.range("C2").value = expand_date_format(report_date)

if (len(prev_pos_sum_df) > 0) or (len(this_pos_sum_df) > 0):

    merge_df = pd.merge(
        left=prev_pos_sum_df, right=this_pos_sum_df,
        left_index=True, right_index=True,
        how="outer", suffixes=["_prev", "_this"]
    )  # type:pd.DataFrame
    merge_df = merge_df.fillna(0)
    s = start_row_num
    pos_comb = []

    # --- step 0: update template from position info
    for (cid, cid_pos) in merge_df.index:
        instrument_id = parse_instrument_id(cid)
        if instrument_id in EXCEPTION_UNIVERSE:
            continue

        pos_comb.append((cid, cid_pos))
        contract_multiplier = instrument_info.get_multiplier(instrument_id)
        instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
        cid_chs = cid.replace(instrument_id, instrument_id_chs)
        cid_name = "{}({})".format(cid_chs, "多" if cid_pos > 0 else "空")

        # --- head
        ws.range("B{}".format(s)).value = cid_name
        ws.range("C{}".format(s)).value = cid
        # --- prev date
        update_r07_prev_date(t_cid=cid, t_cid_pos=cid_pos, t_ws=ws, t_s=s,
                             t_src_df=merge_df, t_margin_tag=margin_tag, t_pos_prop_scale=POS_PROP_SCALE)
        # --- trades
        ws.range("L{}:Q{}".format(s, s)).value = 0
        if (cid, cid_pos) in traded_stats:
            margin_rate = aux_df.at[cid, "margin_rate"] if margin_tag else 1
            update_r07_trades(t_cid=cid, t_cid_pos=cid_pos, t_traded_stats=traded_stats,
                              t_ws=ws, t_s=s, t_contract_multiplier=contract_multiplier, t_margin_rate=margin_rate)
        # --- this date
        update_r07_this_date(t_cid=cid, t_cid_pos=cid_pos, t_ws=ws, t_s=s,
                             t_src_df=merge_df, t_margin_tag=margin_tag, t_pos_prop_scale=POS_PROP_SCALE)
        # --- tail
        ws.range("Z{}".format(s)).value = merge_df.at[(cid, cid_pos), "mkt_val_this"]  # even margin_tag = True, use mkt value

        s += 1
        ws.api.Rows(s).Insert()

    # --- step 1: update template from trades info
    # some intra-day trades may not be found in either prev date or this date
    for (cid, cid_pos), open_close_dfs in traded_stats.items():
        if (cid, cid_pos) not in pos_comb:
            instrument_id = parse_instrument_id(cid)
            contract_multiplier = instrument_info.get_multiplier(instrument_id)
            instrument_id_chs = CHS_NAME_MAPPER[instrument_id]
            cid_chs = cid.replace(instrument_id, instrument_id_chs)
            cid_name = "{}({})".format(cid_chs, "多" if cid_pos > 0 else "空")

            # --- head
            ws.range("B{}".format(s)).value = cid_name
            ws.range("C{}".format(s)).value = cid
            # --- prev date
            ws.range("D{}:K{}".format(s, s)).value = 0
            # --- trades
            margin_rate = aux_df.at[cid, "margin_rate"] if margin_tag else 1
            update_r07_trades(t_cid=cid, t_cid_pos=cid_pos, t_traded_stats=traded_stats,
                              t_ws=ws, t_s=s, t_contract_multiplier=contract_multiplier, t_margin_rate=margin_rate)  # trade
            # --- this date
            ws.range("R{}:Y{}".format(s, s)).value = 0
            # --- tail
            ws.range("Z{}".format(s)).value = 0

            s += 1
            ws.api.Rows(s).Insert()

            # error check
            open_qty = open_close_dfs["open"]["成交量"].sum()
            close_qty = open_close_dfs["open"]["成交量"].sum()
            if open_qty != close_qty:
                print("Warning! open and close qty not match for {}, {} at {} intra-day trades.".format(cid, cid_pos, report_date))
                print("open = {} | close = {} ".format(open_qty, close_qty))

# --- save as xlsx
save_file = template_file[SAVE_NAME_START_IDX:].replace("YYYYMMDD", report_date + VERSION_TAG)
save_path = os.path.join(save_dir, save_file)
if os.path.exists(save_path):
    os.remove(save_path)
wb.save(save_path)
wb.close()
print("| {2} | {0} | {1} | generated |".format(report_name, save_file, dt.datetime.now()))
