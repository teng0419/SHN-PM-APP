import streamlit as st
import pandas as pd
import os

# --- 1. 資料庫初始化 (打地基) ---
# 這裡我們用一個本地的 CSV 檔來模擬資料庫，儲存所有任務的進度。
DB_FILE = 'project_tasks.csv'

def load_or_init_data():
    if not os.path.exists(DB_FILE):
        # 依照你的試算表定義樓層與系統
        floors = ['B2F', 'B1F', '1F', '2F', '3F', '4F', '5F', '6F', '7F', '8F', '9F', '10F', 'R1']
        # 為了示範，先列出主要的幾項弱電系統
        systems = ['資訊網路設備', 'FTTH光纖到府', '監視系統', '門禁系統', 'IP電話交換機', '中央監控']
        stages = ['穿線', '設備安裝', '系統測試']
        
        # 展開成扁平化的任務清單
        data = []
        for f in floors:
            for sys in systems:
                for s in stages:
                    data.append({'樓層': f, '系統': sys, '施工階段': s, '是否完成': False})
        
        df = pd.DataFrame(data)
        df.to_csv(DB_FILE, index=False)
        return df
    else:
        return pd.read_csv(DB_FILE)

# 載入資料
df = load_or_init_data()

# --- 2. 介面設計 (控制面板) ---
st.set_page_config(page_title="友忠好室 - 弱電工程管理", layout="wide")
st.title("🏗️ 友忠好室 - 弱電工程進度管理")

# 建立兩個分頁：一個給主管看大局，一個給現場人員回報
tab1, tab2 = st.tabs(["📊 進度總覽 (Dashboard)", "📱 現場進度回報"])

with tab1:
    st.subheader("整體工程進度")
    # 計算完成率
    total_tasks = len(df)
    completed_tasks = df['是否完成'].sum()
    progress_rate = completed_tasks / total_tasks
    
    # 顯示大數字看板與進度條
    col1, col2 = st.columns(2)
    col1.metric("總任務數", total_tasks)
    col2.metric("已完成", f"{completed_tasks} 項", f"{progress_rate*100:.1f}%")
    st.progress(progress_rate)
    
    # 顯示原始資料表供查閱
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("現場施工回報")
    
    # 建立過濾選單
    col_f, col_s = st.columns(2)
    selected_floor = col_f.selectbox("選擇施工樓層", df['樓層'].unique())
    selected_system = col_s.selectbox("選擇施工系統", df['系統'].unique())
    
    st.markdown("---")
    st.write(f"**目前回報位置：{selected_floor} - {selected_system}**")
    
    # 篩選出符合條件的任務
    mask = (df['樓層'] == selected_floor) & (df['系統'] == selected_system)
    tasks_to_show = df[mask]
    
    # 使用表單讓人員勾選進度
    with st.form("update_form"):
        updated_status = {}
        for index, row in tasks_to_show.iterrows():
            # 建立核取方塊，預設值為資料庫目前的狀態
            is_done = st.checkbox(f"{row['施工階段']}", value=bool(row['是否完成']), key=index)
            updated_status[index] = is_done
            
        # 照片上傳區塊 (目前僅做介面，尚未寫入存檔邏輯)
        st.file_uploader("上傳現場施工照片 (選填)", type=['jpg', 'png'])
        
        submitted = st.form_submit_button("儲存進度")
        
        if submitted:
            # 更新 DataFrame 並存回 CSV
            for idx, status in updated_status.items():
                df.at[idx, '是否完成'] = status
            df.to_csv(DB_FILE, index=False)
            st.success("進度已成功更新！")
            st.rerun() # 重新載入頁面以更新儀表板數字
