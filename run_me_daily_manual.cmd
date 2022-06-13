set trade_date=20220610
python aux_download.py %trade_date%
python aux_intermediary.py %trade_date%
python aux_summary.py %trade_date%
python aux_margin.py %trade_date%
python aux_nav.py %trade_date%
python 00_input_order_inside.py %trade_date%
python 01_input_order_outside.py %trade_date%
python 02_traded_order.py %trade_date%
python 02_traded_order_agg.py %trade_date%
python 03_traded_order_summary.py %trade_date%
python 04_position_details.py %trade_date%
python 05_pnl_summary.py %trade_date%
python 06_risk_control.py %trade_date%
python 07_report.py %trade_date% margin
python 07_report.py %trade_date% no_margin
pause
