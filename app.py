import streamlit as st
import pandas as pd
import os
import datetime

# --- 1. 系統設定 ---
DB_FILE = 'current_project_db.csv'
# 這是系統要求你上傳的清單必須具備的欄位
REQUIRED_COLUMNS = ['系統', '樓層', '地點', '工項', '總數量', '單位']

# --- 2. 核心功能：讀取或初始化資料庫 ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype={'最後更新者': str, '更新時間': str})
        df['最後更新者'] = df['最後更新者'].fillna('')
        df['更新時間'] = df['更新時間'].fillna('')
        return df
    return None

def init_new_project(uploaded_file):
    try:
        # 讀取上傳的檔案 (支援 csv)
        df = pd.read_csv(uploaded_file)
        
        # 檢查欄位是否符合標準架構
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"上傳的檔案缺少必要的欄位：{', '.join(missing_cols)}")
            return False
            
        # 補上進度追蹤的系統欄位
        df['已完成數量'] = 0
        df['最後更新者'] = ''
        df['更新時間'] = ''
        
        # 存成正式的資料庫
        df.to_csv(DB_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"讀取檔案失敗：{e}")
        return False

# 暫時寫死的員工名單 (未來這也可以改成外部讀取)
WORKERS = ["請選擇...", "現場領班", "施工技師", "專案經理", "測試帳號"]

# --- 3. 介面設計 ---
st.set_page_config(page_title="通用工程進度管理", layout="wide")

df = load_data()

# 如果還沒有資料庫，進入「專案初始化」模式
if df is None:
    st.title("🚀 新專案初始化")
    st.info("系統目前沒有專案資料。請先上傳一份整理好的「工作項目清單 (CSV格式)」。")
    st.markdown("""
    **您的 CSV 檔案必須包含以下完整標題（不可有錯字）：**
    `系統` | `樓層` | `地點` | `工項` | `總數量` | `單位`
    """)
    
    uploaded_file = st.file_uploader("上傳專案清單 (.csv)", type=['csv'])
    if uploaded_file is not None:
        if st.button("建立專案資料庫", type="primary"):
            if init_new_project(uploaded_file):
                st.success("專案建立成功！正在載入系統...")
                st.rerun()

# 如果有資料庫，進入「正式管理面板」模式
else:
    st.title("🏗️ 現場工程進度管理系統")
    
    # 新增一個清除專案的按鈕在側邊欄 (方便切換新工程)
    with st.sidebar:
        st.warning("管理員專區")
        if st.button("⚠️ 清除目前專案 (匯入新工程)"):
            os.remove(DB_FILE)
            st.rerun()

    tab1, tab2 = st.tabs(["📱 現場進度回報", "📊 總工程進度追蹤"])

    # ==========================================
    # 分頁 1：現場進度回報
    # ==========================================
    with tab1:
        st.markdown("### 👷 身分確認")
        current_user = st.selectbox("請先選擇您的身分：", WORKERS)
        
        if current_user == "請選擇...":
            st.warning("⚠️ 請先在上方選擇您的名字，才能解鎖填寫功能。")
        else:
            st.markdown("---")
            st.subheader("1. 選擇施工位置")
            
            # 以下所有的選項，都是 APP 讀取你上傳的 CSV 動態生成的
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_system = st.selectbox("施工系統", sorted(df['系統'].unique()))
            filtered_df_sys = df[df['系統'] == selected_system]
            
            with col2:
                selected_floor = st.selectbox("施工樓層", df['樓層'].unique()) # 依照原檔順序
            filtered_df_floor = filtered_df_sys[filtered_df_sys['樓層'] == selected_floor]
            
            with col3:
                # 確保如果有穿線作業，讓它排在最前面
                location_opts = list(filtered_df_floor['地點'].unique())
                if '全層穿線作業' in location_opts:
                    location_opts.insert(0, location_opts.pop(location_opts.index('全層穿線作業')))
                selected_location = st.selectbox("施工地點", location_opts)

            st.markdown("---")
            st.subheader(f"2. 回報 [{selected_floor}] 施工數量")
            final_tasks = filtered_df_floor[filtered_df_floor['地點'] == selected_location]

            if final_tasks.empty:
                st.info("此區域無指定工項。")
            else:
                with st.form("progress_form"):
                    updated_values = {}
                    for index, row in final_tasks.iterrows():
                        st.markdown(f"**{row['工項']}** (應完工總數: {row['總數量']} {row['單位']})")
                        new_val = st.number_input(
                            "目前累計已完成數量",
                            min_value=0,
                            max_value=int(row['總數量']),
                            value=int(row['已完成數量']),
                            step=1,
                            key=f"input_{index}"
                        )
                        updated_values[index] = new_val
                        
                        if pd.notna(row['最後更新者']) and row['最後更新者'] != '':
                            st.caption(f"📝 上次更新: {row['最後更新者']} 於 {row['更新時間']}")
                        st.write("") 

                    submitted = st.form_submit_button("儲存進度", type="primary")
                    
                    if submitted:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for idx, val in updated_values.items():
                            if df.at[idx, '已完成數量'] != val:
                                df.at[idx, '已完成數量'] = val
                                df.at[idx, '最後更新者'] = current_user
                                df.at[idx, '更新時間'] = now
                        df.to_csv(DB_FILE, index=False)
                        st.success("數量已成功更新！")
                        st.rerun()

    # ==========================================
    # 分頁 2：統計總工程進度
    # ==========================================
    with tab2:
        st.subheader("整體進度概況")
        total_tasks = len(df)
        completed_tasks = len(df[df['已完成數量'] >= df['總數量']])
        progress_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        col_a, col_b = st.columns(2)
        col_a.metric("全區總列管工項數", total_tasks)
        col_b.metric("已完工項目", f"{completed_tasks} 項", f"{progress_rate*100:.1f}%")
        st.progress(progress_rate)
        
        st.markdown("---")
        st.subheader("各系統完工狀態盤點")
        
        filter_floor = st.selectbox("依樓層篩選查看", ["全部"] + list(df['樓層'].unique()))
        
        display_df = df.copy()
        display_df['狀態'] = display_df.apply(
            lambda x: '✅ 完工' if x['已完成數量'] >= x['總數量'] else ('⏳ 施工中' if x['已完成數量'] > 0 else '❌ 未開始'), 
            axis=1
        )
        
        if filter_floor != "全部":
            display_df = display_df[display_df['樓層'] == filter_floor]
        
        st.dataframe(
            display_df[['狀態', '樓層', '系統', '地點', '工項', '已完成數量', '總數量', '單位', '最後更新者', '更新時間']], 
            use_container_width=True,
            hide_index=True
        )
