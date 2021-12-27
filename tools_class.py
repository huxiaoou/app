from setup import *
from skyrim.whiterun import CCalendar


class CInstrumentInfo(object):
    def __init__(self, t_path):
        self.m_info_df = pd.read_excel(t_path).set_index("instrumentId")

    def get_multiplier(self, t_instrument_id):
        return self.m_info_df.at[t_instrument_id, "contractMultiplier"]

    def get_market_chs(self, t_instrument_id):
        market_eng = self.m_info_df.at[t_instrument_id, "exchangeId"]
        market_chs = {
            "DCE": "大商所",
            "CZCE": "郑商所",
            "SHFE": "上期所",
            "INE": "上海能源",
        }[market_eng]
        return market_chs


class CNAV(object):
    def __init__(self, t_nav_srs: pd.Series, t_annual_rf_rate: float, t_freq: str):
        self.m_nav_srs = t_nav_srs
        self.m_rtn_srs = (np.log(t_nav_srs / t_nav_srs.shift(1)) * 100).fillna(0)
        self.m_obs = len(t_nav_srs)

        self.m_annual_factor = {
            "D": 252,
            "W": 52,
            "M": 12,
            "Y": 1,
        }[t_freq]

        self.m_annual_rf_rate = t_annual_rf_rate
        self.m_annual_return = 0
        self.m_hold_period_return = 0
        self.m_sharpe_ratio = 0
        self.m_max_drawdown = 0
        self.m_max_drawdown_date = self.m_nav_srs.index[0]

        self.m_max_drawdown_prev_high_date = ""
        self.m_max_drawdown_re_break_date = ""
        self.m_max_drawdown_duration = {"natural": 0, "trade": 0}
        self.m_max_drawdown_recover_duration = {"natural": 0, "trade": 0}

    def cal_hold_period_return(self):
        self.m_hold_period_return = (self.m_nav_srs.iloc[-1] / self.m_nav_srs.iloc[0] - 1) * 100
        return 0

    def cal_annual_return(self):
        self.m_annual_return = self.m_rtn_srs.mean() * self.m_annual_factor
        return 0

    def cal_sharpe_ratio0(self):
        diff_srs = self.m_rtn_srs - self.m_annual_rf_rate / self.m_annual_factor
        mu = diff_srs.mean()
        sd = diff_srs.std()
        self.m_sharpe_ratio = mu / sd * np.sqrt(self.m_annual_factor)
        print("SR-HXO = {:.2f}".format(self.m_sharpe_ratio))
        return 0

    def cal_sharpe_ratio1(self):
        _hpr = (self.m_nav_srs.iloc[-1] / self.m_nav_srs.iloc[0] - 1) * 100
        _anr = _hpr / len(self.m_nav_srs) * self.m_annual_factor - self.m_annual_rf_rate
        sd = self.m_rtn_srs.std()
        self.m_sharpe_ratio = _anr / sd / np.sqrt(self.m_annual_factor)
        print("SR-FYB = {:.2f}".format(self.m_sharpe_ratio))
        return 0

    def cal_max_drawdown(self):
        nav_hist_high = 1.0
        self.m_max_drawdown = 0
        for trade_date in self.m_nav_srs.index:
            nav_val = self.m_nav_srs[trade_date]
            if nav_val > nav_hist_high:
                nav_hist_high = nav_val
            # new_drawback = nav_hist_high - nav_val  # absolute way
            new_drawback = (1 - nav_val / nav_hist_high) * 100  # relative way
            if new_drawback >= self.m_max_drawdown:
                self.m_max_drawdown = new_drawback
                self.m_max_drawdown_date = trade_date

        prev_mdd_srs = self.m_nav_srs[self.m_nav_srs.index < self.m_max_drawdown_date]  # type:pd.Series
        this_mdd_srs = self.m_nav_srs[self.m_nav_srs.index >= self.m_max_drawdown_date]  # type:pd.Series
        self.m_max_drawdown_prev_high_date = prev_mdd_srs.idxmax()
        prev_high_value = prev_mdd_srs.max()
        re_break_idx = this_mdd_srs >= prev_high_value
        if any(re_break_idx):
            re_break_srs = this_mdd_srs[re_break_idx]
            self.m_max_drawdown_re_break_date = re_break_srs.index[0]
        else:
            self.m_max_drawdown_re_break_date = "Never"
        return 0

    def cal_mdd_duration(self, t_calendar: CCalendar):
        # mdd duration
        _head_date = self.m_max_drawdown_prev_high_date.replace("-", "")
        _tail_date = self.m_max_drawdown_date.replace("-", "")
        self.m_max_drawdown_duration["trade"] = t_calendar.get_sn(_tail_date) - t_calendar.get_sn(_head_date)
        self.m_max_drawdown_duration["natural"] = (dt.datetime.strptime(_tail_date, "%Y%m%d") - dt.datetime.strptime(_head_date, "%Y%m%d")).days

        # recover duration
        if self.m_max_drawdown_re_break_date == "Never":
            self.m_max_drawdown_recover_duration["trade"] = np.inf
            self.m_max_drawdown_recover_duration["natural"] = np.inf
        else:
            _head_date = self.m_max_drawdown_date.replace("-", "")
            _tail_date = self.m_max_drawdown_re_break_date.replace("-", "")
            self.m_max_drawdown_recover_duration["trade"] = t_calendar.get_sn(_tail_date) - t_calendar.get_sn(_head_date)
            self.m_max_drawdown_recover_duration["natural"] = (dt.datetime.strptime(_tail_date, "%Y%m%d") - dt.datetime.strptime(_head_date, "%Y%m%d")).days
        return 0

    def to_dict(self):
        d = {
            "hold_period_return": self.m_hold_period_return,
            "annual_return": self.m_annual_return,
            "sharpe_ratio": self.m_sharpe_ratio,
            "max_drawdown": self.m_max_drawdown,
            "max_drawdown_date": self.m_max_drawdown_date,
            "prev_high_date": self.m_max_drawdown_prev_high_date,
            "re_break_date": self.m_max_drawdown_re_break_date,
            "mdd_duration_t": self.m_max_drawdown_duration["trade"],
            "mdd_duration_n": self.m_max_drawdown_duration["natural"],
            "recover_duration_t": self.m_max_drawdown_recover_duration["trade"],
            "recover_duration_n": self.m_max_drawdown_recover_duration["natural"],
        }
        return d

    def display(self):
        print("| HPR = {:>7.4f} | AnnRtn = {:>7.4f} | MDD = {:>7.2f} | SPR = {:>7.4f} | ".format(
            self.m_hold_period_return,
            self.m_annual_return,
            self.m_max_drawdown,
            self.m_sharpe_ratio,
        ))
        return 0
