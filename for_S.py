import streamlit as st
import pandas as pd
import numpy as np
import re

st.set_page_config(page_title="31P代谢分析工具", layout="wide")
st.title("基于31P-MRS数据的宽表&比值自动分析工具")

uploaded_file = st.file_uploader("请上传原始Excel文件（必须包含'Metab', 'Source.Name', 'Area'三列）", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # 1. 标准化Metab列
    metab_map = {
        "PCr": 'PCr',
        'bATP': 'bATP',
        'PE': 'P_E',
        'PC': 'P_C',
        'GPE': 'GPE',
        'GPC': 'GPC',
        '*NADH': 'NADH',
        '*A_ATP': 'A_ATP',
        '*Pi_D': 'Pi',
        '*gATP_D': 'gATP',
    }
    def normalize_metab(x):
        return metab_map.get(x, x)
    df['Metab'] = df['Metab'].astype(str).map(normalize_metab)

    # 2. pivot
    pivot = df.pivot_table(
        index='Source.Name',
        columns='Metab',
        values='Area',
        aggfunc='sum'
    ).reset_index()

    required_cols = ['PCr', 'bATP', 'P_E', 'P_C', 'GPE', 'GPC', 'NADH', 'A_ATP', 'Pi', 'gATP']
    for col in required_cols:
        if col not in pivot.columns:
            pivot[col] = np.nan

    # 3. 计算汇总项
    pivot['TPC1'] = pivot[required_cols].sum(axis=1)
    pivot['PME'] = pivot['P_E'] + pivot['P_C']
    pivot['PDE'] = pivot['GPE'] + pivot['GPC']
    pivot['NTP'] = pivot['A_ATP'] + pivot['gATP']
    pivot['MD'] = pivot['PME'] + pivot['PDE']

    def safe_div(a, b):
        return np.where(b == 0, np.nan, a / b)

    # 4. 示例比值（你可以在ratio_dict里加你想要的所有比值）
    ratio_dict = {
        'A_ATP/MD':   ('A_ATP', 'MD'),
        'A_ATP/NTP':  ('A_ATP', 'NTP'),
        'A_ATP/PDE':  ('A_ATP', 'PDE'),
        'A_ATP/PME':  ('A_ATP', 'PME'),
        'A_ATP/Pi':   ('A_ATP', 'Pi'),
        'A_ATP/TPC1': ('A_ATP', 'TPC1'),
        'A_ATP/gATP': ('A_ATP', 'gATP'),
        'GPC/A_ATP':  ('GPC', 'A_ATP'),
        'GPC/MD':     ('GPC', 'MD'),
        'GPC/NTP':    ('GPC', 'NTP'),
        'GPC/PDE':    ('GPC', 'PDE'),
        'GPC/PME':    ('GPC', 'PME'),
        'GPC/Pi':     ('GPC', 'Pi'),
        'GPC/TPC1':   ('GPC', 'TPC1'),
        'GPC/gATP':   ('GPC', 'gATP'),
        'GPE/A_ATP':  ('GPE', 'A_ATP'),
        'GPE/GPC':    ('GPE', 'GPC'),
        'GPE/MD':     ('GPE', 'MD'),
        'GPE/NTP':    ('GPE', 'NTP'),
        'GPE/PDE':    ('GPE', 'PDE'),
        'GPE/PME':    ('GPE', 'PME'),
        'GPE/Pi':     ('GPE', 'Pi'),
        'GPE/TPC1':   ('GPE', 'TPC1'),
        'GPE/gATP':   ('GPE', 'gATP'),
        'NADH/A_ATP': ('NADH', 'A_ATP'),
        'NADH/MD':    ('NADH', 'MD'),
        'NADH/NTP':   ('NADH', 'NTP'),
        'NADH/PDE':   ('NADH', 'PDE'),
        'NADH/PME':   ('NADH', 'PME'),
        'NADH/Pi':    ('NADH', 'Pi'),
        'NADH/TPC1':  ('NADH', 'TPC1'),
        'NADH/gATP':  ('NADH', 'gATP'),
        'NTP/TPC1':   ('NTP', 'TPC1'),
        'PDE/MD':     ('PDE', 'MD'),
        'PDE/NTP':    ('PDE', 'NTP'),
        'PDE/TPC1':   ('PDE', 'TPC1'),
        'PME/MD':     ('PME', 'MD'),
        'PME/NTP':    ('PME', 'NTP'),
        'PME/PDE':    ('PME', 'PDE'),
        'PME/TPC1':   ('PME', 'TPC1'),
        'P_C/A_ATP':  ('P_C', 'A_ATP'),
        'P_C/MD':     ('P_C', 'MD'),
        'P_C/NTP':    ('P_C', 'NTP'),
        'P_C/PDE':    ('P_C', 'PDE'),
        'P_C/GPC':    ('P_C', 'GPC'),
        'P_C/GPE':    ('P_C', 'GPE'),
        'P_C/PME':    ('P_C', 'PME'),
        'P_C/Pi':     ('P_C', 'Pi'),
        'P_C/TPC1':   ('P_C', 'TPC1'),
        'P_C/gATP':   ('P_C', 'gATP'),
        'P_E/A_ATP':  ('P_E', 'A_ATP'),
        'P_E/MD':     ('P_E', 'MD'),
        'P_E/NTP':    ('P_E', 'NTP'),
        'P_E/PDE':    ('P_E', 'PDE'),
        'P_E/GPC':    ('P_E', 'GPC'),
        'P_E/GPE':    ('P_E', 'GPE'),
        'P_E/PME':    ('P_E', 'PME'),
        'P_E/P_C':    ('P_E', 'P_C'),
        'P_E/Pi':     ('P_E', 'Pi'),
        'P_E/TPC1':   ('P_E', 'TPC1'),
        'P_E/gATP':   ('P_E', 'gATP'),
        'Pi/A_ATP':   ('Pi', 'A_ATP'),
        'Pi/MD':      ('Pi', 'MD'),
        'Pi/NTP':     ('Pi', 'NTP'),
        'Pi/PDE':     ('Pi', 'PDE'),
        'Pi/PME':     ('Pi', 'PME'),
        'Pi/TPC1':    ('Pi', 'TPC1'),
        'Pi/gATP':    ('Pi', 'gATP'),
        'gATP/A_ATP': ('gATP', 'A_ATP'),
        'gATP/MD':    ('gATP', 'MD'),
        'gATP/NTP':   ('gATP', 'NTP'),
        'gATP/PDE':   ('gATP', 'PDE'),
        'gATP/PME':   ('gATP', 'PME'),
        'gATP/Pi':    ('gATP', 'Pi'),
        'gATP/TPC1':  ('gATP', 'TPC1'),
        'bATP/MD':   ('bATP', 'MD'),
        'bATP/NTP':  ('bATP', 'NTP'),
        'bATP/PDE':  ('bATP', 'PDE'),
        'bATP/PME':  ('bATP', 'PME'),
        'bATP/Pi':   ('bATP', 'Pi'),
        'bATP/TPC1': ('bATP', 'TPC1'),
        'bATP/gATP': ('bATP', 'gATP'),
        'PCr/MD':   ('PCr', 'MD'),
        'PCr/NTP':  ('PCr', 'NTP'),
        'PCr/PDE':  ('PCr', 'PDE'),
        'PCr/PME':  ('PCr', 'PME'),
        'PCr/Pi':   ('PCr', 'Pi'),
        'PCr/TPC1': ('PCr', 'TPC1'),
        'PCr/gATP': ('PCr', 'gATP'),


    }

    # 批量生成所有比值
    for name, (numer, denom) in ratio_dict.items():
        if numer in pivot.columns and denom in pivot.columns:
            pivot[name] = safe_div(pivot[numer], pivot[denom])
        else:
            pivot[name] = np.nan  # 没有的列也补齐
    # 可按自己需求输出所有比值与原始宽表
    output_cols = ['Source.Name'] + list(ratio_dict.keys())
    pivot_out = pivot[output_cols] if set(output_cols).issubset(pivot.columns) else pivot
    print(pivot.index)
        # 5. 美化表头

    def rename_col(col):
        col = re.sub(r"\bP_E\b", "PE", col)
        col = re.sub(r"\bP_C\b", "PC", col)
        col = re.sub(r"\bTPC1\b", "TPC", col)
        col = re.sub(r"\bMD\b", "(PME+PDE)", col)
        col = re.sub(r"\bgATP\b", "γ-ATP", col)
        col = re.sub(r"\bA_ATP\b", "α-ATP", col)
        col = re.sub(r"\bbATP\b", "β-ATP", col)
        return col

    st.success("处理完毕，结果宽表预览：")
    st.dataframe(pivot)

    # 提供下载按钮
    st.download_button(
        label="下载Excel结果",
        data=pivot.to_excel(index=False, engine='openpyxl'),
        file_name="31P分析结果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("请先上传一个原始数据Excel文件")

