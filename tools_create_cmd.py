report_date = "20200814"
with open("run_me_daily.cmd", "w+") as f:
    f.write("python aux_download.py {}\n".format(report_date))
    f.write("python aux_intermediary.py {}\n".format(report_date))
    f.write("python aux_summary.py {}\n".format(report_date))
    f.write("python 00_input_order_inside.py {}\n".format(report_date))
    f.write("python 01_input_order_outside.py {}\n".format(report_date))
    f.write("python 02_traded_order.py {}\n".format(report_date))
    f.write("python 03_traded_order_summary.py {}\n".format(report_date))
    f.write("python 04_position_details.py {}\n".format(report_date))
    f.write("python 05_pnl_summary.py {}\n".format(report_date))
    f.write("python 06_risk_control.py {}\n".format(report_date))
    f.write("python 07_report.py {} margin\n".format(report_date))
    f.write("python 07_report.py {} no_margin\n".format(report_date))
