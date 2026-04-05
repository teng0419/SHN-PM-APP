import streamlit as st
import pandas as pd
import os

# --- 1. 資料庫初始化 (建立假設的測試資料) ---
DB_FILE = 'master_tasks_mock.csv'

def load_or_init_data():
    if not os.path.exists(DB_FILE):
        # 這裡就是我們假設的資料結構，包含你提到的「地點」與「總數量/已完成」
        data = [
            {'系統': '監視系統', '樓層': '1F', '地點': '大廳入口', '工項': '網路紅外線半球型攝影機', '總數量': 2, '已完成數量': 0, '單位': '台'},
            {'系統': '監視系統', '樓層': '1F', '地點': '車道口', '工項': '車牌辨識攝影機', '總數量': 1, '已完成數量': 0, '單位': '台'},
            {'系統': '監視系統', '樓層': '2F', '地點': 'A201戶門口', '工項': '網路紅外線半球型攝影機', '總數量': 1, '已完成數量': 0, '單位': '台'},
            {'系統': '門禁系統', '樓層': '1F', '地點': '大廳大門', '工項': '讀卡機與電子鎖', '總數量': 1, '已完成數量': 0, '單位': '組'},
            {'系統': '門禁系統', '樓層': 'B1F', '地點': 'A棟梯廳', '工項': '讀卡機', '總數量': 2, '已完成數量': 0, '單位': '組'},
            {'系統': 'FTTH光纖到府', '樓層': '1F', '地點': '電信機房', '工項': '光纖引進線', '總數量': 150, '已完成數量': 0, '單位': '米'},
        ]
        df = pd.DataFrame(data)
        df.to_csv(DB_FILE, index=False)
        return df
    else:
        return pd.read_csv(DB_FILE)

df = load_or_init_data()

# --- 2. 介面設計 (漏斗式控制面板) ---
st.set_page_config(page_title="工程進度回報測試", layout="centered")
st.title("🏗️ 現場進度回報 (動線測試版)")

st.subheader("1. 選擇施工位置")
# 使用三個並排的選單，並產生連動過濾效果
col1, col2, col3 = st.columns(3)

with col1:
    selected_system = st.selectbox("施工系統", df['系統'].unique())

# 根據選到的系統，過濾出該系統有安排的樓層
filtered_df_sys = df[df['系統'] == selected_system]
with col2:
    selected_floor = st.selectbox("施工樓層", filtered_df_sys['樓層'].unique())

# 根據系統與樓層，過濾出該區域有的地點
filtered_df_floor = filtered_df_sys[filtered_df_sys['樓層'] == selected_floor]
with col3:
    selected_location = st.selectbox("施工地點", filtered_df_floor['地點'].unique())

st.markdown("---")
st.subheader("2. 回報施工數量")

# 最終篩選出該地點需要做的所有工項
final_tasks = filtered_df_floor[filtered_df_floor['地點'] == selected_location]

with st.form("progress_form"):
    updated_values = {}
    
    # 將該地點的工項一條一條列出來讓使用者填寫
    for index, row in final_tasks.iterrows():
        # 顯示工項名稱與總數量
        st.markdown(f"**{row['工項']}** (應完工總數: {row['總數量']} {row['單位']})")
        
        # 建立數字輸入框，預設顯示上次儲存的已完成數量
        new_val = st.number_input(
            "目前已完成",
            min_value=0,
            max_value=int(row['總數量']),
            value=int(row['已完成數量']),
            step=1,
            key=f"input_{index}"
        )
        updated_values[index] = new_val
        st.write("") # 排版留白

    # 提交按鈕
    submitted = st.form_submit_button("儲存進度", type="primary")
    
    if submitted:
        # 將填寫的數字寫回 DataFrame 並存檔
        for idx, val in updated_values.items():
            df.at[idx, '已完成數量'] = val
        df.to_csv(DB_FILE, index=False)
        st.success("數量已成功更新！")
        st.rerun()
