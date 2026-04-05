import streamlit as st
import pandas as pd
import os
import datetime

# --- 1. 資料庫初始化 ---
DB_FILE = 'master_tasks_mock.csv'

def load_or_init_data():
    if not os.path.exists(DB_FILE):
        data = [
            {'系統': '監視系統', '樓層': '1F', '地點': '大廳入口', '工項': '網路紅外線半球型攝影機', '總數量': 2, '已完成數量': 0, '單位': '台', '最後更新者': '', '更新時間': ''},
            {'系統': '監視系統', '樓層': '1F', '地點': '車道口', '工項': '車牌辨識攝影機', '總數量': 1, '已完成數量': 0, '單位': '台', '最後更新者': '', '更新時間': ''},
            {'系統': '監視系統', '樓層': '2F', '地點': 'A201戶門口', '工項': '網路紅外線半球型攝影機', '總數量': 1, '已完成數量': 0, '單位': '台', '最後更新者': '', '更新時間': ''},
            {'系統': '門禁系統', '樓層': '1F', '地點': '大廳大門', '工項': '讀卡機與電子鎖', '總數量': 1, '已完成數量': 0, '單位': '組', '最後更新者': '', '更新時間': ''},
            {'系統': '門禁系統', '樓層': 'B1F', '地點': 'A棟梯廳', '工項': '讀卡機', '總數量': 2, '已完成數量': 0, '單位': '組', '最後更新者': '', '更新時間': ''},
            {'系統': 'FTTH光纖到府', '樓層': '1F', '地點': '電信機房', '工項': '光纖引進線', '總數量': 150, '已完成數量': 0, '單位': '米', '最後更新者': '', '更新時間': ''},
        ]
        df = pd.DataFrame(data)
        df.to_csv(DB_FILE, index=False)
        return df
    else:
        # 為了相容舊版資料庫，如果沒有新欄位就補上
        df = pd.read_csv(DB_FILE)
        if '最後更新者' not in df.columns:
            df['最後更新者'] = ''
            df['更新時間'] = ''
        return df

df = load_or_init_data()

# 假設的施工人員名單
WORKERS = ["請選擇...", "領班阿明 (監視)", "師傅老王 (門禁)", "主任陳sir", "測試帳號"]

# --- 2. 介面設計 ---
st.set_page_config(page_title="友忠好室 - 進度管理", layout="wide")
st.title("🏗️ 友忠好室 - 弱電工程進度管理")

tab1, tab2 = st.tabs(["📱 現場進度回報", "📊 統計總工程進度"])

# ==========================================
# 分頁 1：現場進度回報 (加入身分驗證與修正機制)
# ==========================================
with tab1:
    # --- 新增：打卡鐘 (使用者識別) ---
    st.markdown("### 👷 身分確認")
    current_user = st.selectbox("請先選擇您的身分，再進行進度回報：", WORKERS)
    
    if current_user == "請選擇...":
        st.warning("⚠️ 請先在上方選擇您的名字，才能解鎖填寫功能。")
    else:
        st.info(f"您好，**{current_user}**！如果發現之前填錯，只要在這裡把數字改回正確的，再按一次儲存即可覆蓋舊資料。")
        
        st.markdown("---")
        st.subheader("1. 選擇施工位置")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_system = st.selectbox("施工系統", df['系統'].unique())
        filtered_df_sys = df[df['系統'] == selected_system]
        with col2:
            selected_floor = st.selectbox("施工樓層", filtered_df_sys['樓層'].unique())
        filtered_df_floor = filtered_df_sys[filtered_df_sys['樓層'] == selected_floor]
        with col3:
            selected_location = st.selectbox("施工地點", filtered_df_floor['地點'].unique())

        st.markdown("---")
        st.subheader("2. 回報/修正 施工數量")
        final_tasks = filtered_df_floor[filtered_df_floor['地點'] == selected_location]

        with st.form("progress_form"):
            updated_values = {}
            for index, row in final_tasks.iterrows():
                st.markdown(f"**{row['工項']}** (應完工總數: {row['總數量']} {row['單位']})")
                # 這裡的 number_input 允許使用者隨意調高或調低數字，達到修正的目的
                new_val = st.number_input(
                    "目前累計已完成數量",
                    min_value=0,
                    max_value=int(row['總數量']),
                    value=int(row['已完成數量']),
                    step=1,
                    key=f"input_{index}"
                )
                updated_values[index] = new_val
                
                # 顯示一下這筆資料上次是誰改的
                if pd.notna(row['最後更新者']) and row['最後更新者'] != '':
                    st.caption(f"📝 上次更新: {row['最後更新者']} 於 {row['更新時間']}")
                st.write("") 

            submitted = st.form_submit_button("儲存/修正進度", type="primary")
            
            if submitted:
                # 記錄當下時間
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for idx, val in updated_values.items():
                    # 只有當數字真的有變動時，才更新「最後更新者」和「時間」
                    if df.at[idx, '已完成數量'] != val:
                        df.at[idx, '已完成數量'] = val
                        df.at[idx, '最後更新者'] = current_user
                        df.at[idx, '更新時間'] = now
                df.to_csv(DB_FILE, index=False)
                st.success("數量已成功更新！")
                st.rerun()

# ==========================================
# 分頁 2：統計總工程進度 (加入追蹤欄位)
# ==========================================
with tab2:
    st.subheader("整體工程進度概況")
    total_tasks = len(df)
    completed_tasks = len(df[df['已完成數量'] >= df['總數量']])
    progress_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
    
    col_a, col_b = st.columns(2)
    col_a.metric("總列管工項數", total_tasks)
    col_b.metric("已 100% 完工項目", f"{completed_tasks} 項", f"{progress_rate*100:.1f}%")
    st.progress(progress_rate)
    
    st.markdown("---")
    st.subheader("各系統完工狀態盤點 (含責任追蹤)")
    
    display_df = df.copy()
    display_df['狀態'] = display_df.apply(
        lambda x: '✅ 完工' if x['已完成數量'] >= x['總數量'] else ('⏳ 施工中' if x['已完成數量'] > 0 else '❌ 未開始'), 
        axis=1
    )
    
    # 顯示的表格增加了「最後更新者」與「更新時間」
    st.dataframe(
        display_df[['狀態', '系統', '樓層', '地點', '工項', '已完成數量', '總數量', '最後更新者', '更新時間']], 
        use_container_width=True,
        hide_index=True
    )
