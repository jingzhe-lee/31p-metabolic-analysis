import streamlit as st
import pandas as pd
import numpy as np
import re
import io

st.set_page_config(page_title="31P代谢分析工具", layout="wide")
st.title("基于SpectroView的31P-MRS原始数据比值分析工具")

# 1. 固定“展示名”选项
DISPLAY_NAMES = [
    "PCr", "β-ATP", "PE", "PC", "GPE", "GPC", "NADH", "α-ATP", "γ-ATP", "Pi"
]

# 2. “展示名”->“标准分析名”映射
DISPLAY2ANALYSIS = {
    "PCr": "PCr",
    "β-ATP": "bATP",
    "PE": "P_E",
    "PC": "P_C",
    "GPE": "GPE",
    "GPC": "GPC",
    "NADH": "NADH",
    "α-ATP": "A_ATP",
    "γ-ATP": "gATP",
    "Pi": "Pi"
}

# 3. “标准分析名”->“展示名” 反向映射，供后续结果列名美化
ANALYSIS2DISPLAY = {v: k for k, v in DISPLAY2ANALYSIS.items()}

uploaded_file = st.file_uploader("请上传原始Excel文件（必须包含'Metab', 'Source.Name', 'Area'三列）", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("原始数据已上传！")

    # 4. 收集所有原始Metab名
    unique_metabs = sorted(df['Metab'].astype(str).unique())

    # 5. 让用户选择原始名对应的展示名（每一行一个下拉菜单）
    st.write("请为每个原始名选择标准‘展示名’（如不在列表则选‘——’忽略该项）：")
    mapping = {}
    for raw in unique_metabs:
        disp = st.selectbox(
            f"{raw} →",
            options=["——"] + DISPLAY_NAMES,
            key=f"select_{raw}"
        )
        if disp != "——":
            mapping[raw] = disp

    # 必须至少有一项映射
    if not mapping:
        st.warning("请至少选择一个代谢物映射。")
        st.stop()

    # 6. 应用用户自定义映射，把Metab原始名→展示名（新加一列）
    df['展示名'] = df['Metab'].map(mapping)

    # 丢弃无映射的行
    df = df[~df['展示名'].isnull()].copy()

    # 7. 展示名→标准分析名
    df['标准分析名'] = df['展示名'].map(DISPLAY2ANALYSIS)

    # 8. 用标准分析名透视表
    pivot = df.pivot_table(
        index='Source.Name',
        columns='标准分析名',
        values='Area',
        aggfunc='sum'
    ).reset_index()

    # 保证所有分析列都存在
    required_cols = ['PCr', 'bATP', 'P_E', 'P_C', 'GPE', 'GPC', 'NADH', 'A_ATP', 'Pi', 'gATP']
    for col in required_cols:
        if col not in pivot.columns:
            pivot[col] = np.nan

    # 派生变量
    pivot['TPC'] = pivot[required_cols].sum(axis=1)
    pivot['PME'] = pivot['P_E'] + pivot['P_C']
    pivot['PDE'] = pivot['GPE'] + pivot['GPC']
    pivot['NTP'] = pivot['A_ATP'] + pivot['gATP']
    pivot['(PME+PDE)'] = pivot['PME'] + pivot['PDE']

    # 比值示例
    def safe_div(a, b):
        return np.where(b == 0, np.nan, a / b)
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
    # 生成所有比值
    for name, (numer, denom) in ratio_dict.items():
        if numer in pivot.columns and denom in pivot.columns:
            pivot[name] = safe_div(pivot[numer], pivot[denom])
        else:
            pivot[name] = np.nan

    # 9. 美化所有列名为展示名（包括比值名）
    def beautify_col(col):
        # 先标准列
        if col in ANALYSIS2DISPLAY:
            return ANALYSIS2DISPLAY[col]
        # 比值列
        col = re.sub(r"\b(P_E|PE|P_C|PC|A_ATP|α-ATP|gATP|γ-ATP|bATP|β-ATP|GPE|GPC|NADH|Pi|TPC|NTP|PME|PDE)\b",
                     lambda m: ANALYSIS2DISPLAY.get(DISPLAY2ANALYSIS.get(m.group(1), m.group(1)), m.group(1)), col)
        return col

    pivot.columns = [beautify_col(c) if c != 'Source.Name' else c for c in pivot.columns]

    # 10. 展示与导出
    st.success("处理完毕，结果宽表预览：")
    st.dataframe(pivot)

    # 下载
    output = io.BytesIO()
    pivot.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    st.download_button(
        label="下载Excel结果",
        data=output.getvalue(),
        file_name="31P分析结果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
