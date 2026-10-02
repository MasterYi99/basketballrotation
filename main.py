import streamlit as st
import time

st.set_page_config(page_title="籃球球員輪替管理系統", layout="wide")

# 1. 預設球員名單
INITIAL_ROSTER = [
    "溫少宇 G",   
    "田佳右 G",
    "洪大洋 SF",
    "潘瑞鐶 PF",
    "楊茜評 C",
    "邱泓森 C",
    "郭志峯 SF",
    "魏志強 C",
    "林育緯 SF",
    "蔡孟霖 G",
    "鍾岳甫 G",
    "許哲翊 SF",
    "梁瑞鈞 G"
]

# 2. 初始化 / 重置函式
def init_game(reset_lineup=False):
    """
    reset_lineup: 
      - True: 恢復成預設前5人先發
      - False: 保持目前場上/替補陣容，僅秒數歸零
    """
    now = time.time()
    st.session_state.game_running = False
    st.session_state.selected_court = None
    st.session_state.selected_bench = None

    if reset_lineup or "on_court" not in st.session_state:
        st.session_state.on_court = {
            name: {"total_sec": 0, "in_time": None} for name in INITIAL_ROSTER[:5]
        }
        st.session_state.bench = {
            name: {"total_sec": 0, "in_time": None} for name in INITIAL_ROSTER[5:]
        }
    else:
        # 只歸零秒數，維持現有陣容
        for data in st.session_state.on_court.values():
            data["total_sec"] = 0
            data["in_time"] = None
        for data in st.session_state.bench.values():
            data["total_sec"] = 0
            data["in_time"] = None

# 頁面初次載入
if "on_court" not in st.session_state:
    init_game(reset_lineup=True)

# 工具函式：格式化時間 (分:秒)
def format_time(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"

# 工具函式：計算球員當前累計時間
def get_current_time(player_data):
    if st.session_state.game_running and player_data["in_time"] is not None:
        elapsed = time.time() - player_data["in_time"]
        return player_data["total_sec"] + elapsed
    return player_data["total_sec"]

# 比賽計時控制：開始 / 暫停
def toggle_game():
    now = time.time()
    if st.session_state.game_running:
        for name, data in st.session_state.on_court.items():
            if data["in_time"] is not None:
                data["total_sec"] += (now - data["in_time"])
                data["in_time"] = None
        st.session_state.game_running = False
    else:
        for name, data in st.session_state.on_court.items():
            data["in_time"] = now
        st.session_state.game_running = True

# 換人邏輯
def substitute(court_player, bench_player):
    now = time.time()
    
    # 結算退場球員
    c_data = st.session_state.on_court.pop(court_player)
    if st.session_state.game_running and c_data["in_time"] is not None:
        c_data["total_sec"] += (now - c_data["in_time"])
    c_data["in_time"] = None
    st.session_state.bench[court_player] = c_data

    # 換上場球員
    b_data = st.session_state.bench.pop(bench_player)
    b_data["in_time"] = now if st.session_state.game_running else None
    st.session_state.on_court[bench_player] = b_data

    # 清空選取狀態
    st.session_state.selected_court = None
    st.session_state.selected_bench = None

# --- UI 介面 ---
st.title("🏀 籃球輪替與上場時間管理")

# 頂部控制面板
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1, 1, 1])

with ctrl_col1:
    status_icon = "🟢 進行中" if st.session_state.game_running else "🔴 暫停中"
    st.markdown(f"### 比賽狀態：{status_icon}")

with ctrl_col2:
    if st.button("▶️ 開始比賽" if not st.session_state.game_running else "⏸️ 暫停比賽", use_container_width=True, type="primary"):
        toggle_game()
        st.rerun()

with ctrl_col3:
    if st.button("🔄 刷新秒數", use_container_width=True):
        st.rerun()

with ctrl_col4:
    # 秒數重置彈窗控制
    @st.dialog("⚠️ 重置選項確認")
    def confirm_reset_dialog():
        st.write("請選擇要執行的重置方式：")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⏱️ 僅秒數歸零", use_container_width=True, help="保留目前場上/替補球員，只將時間歸零"):
                init_game(reset_lineup=False)
                st.rerun()
        with col_b:
            if st.button("🚨 全場重置", use_container_width=True, help="秒數歸零，且先發陣容恢復成預設名單"):
                init_game(reset_lineup=True)
                st.rerun()

    if st.button("⏹️ 重置 / 歸零", use_container_width=True):
        confirm_reset_dialog()

# 選取提示
c_sel = st.session_state.selected_court
b_sel = st.session_state.selected_bench
if c_sel and not b_sel:
    st.info(f"👉 已選取場上球員：**{c_sel}**，請點選欲換上的替補球員。")
elif b_sel and not c_sel:
    st.info(f"👉 已選取替補球員：**{b_sel}**，請點選欲換下的場上球員。")
else:
    st.caption("💡 提示：點擊一名「場上球員」與一名「替補球員」即可立即完成輪替交換。")

st.divider()

col_court, col_bench = st.columns(2)

# --- 場上陣容 (5人) ---
with col_court:
    st.subheader(f"⚡ 場上陣容 ({len(st.session_state.on_court)}/5)")
    for name, data in list(st.session_state.on_court.items()):
        current_sec = get_current_time(data)
        is_selected = (st.session_state.selected_court == name)
        
        btn_label = f"🟢 {name}  |  ⏱️ {format_time(current_sec)} {' [已選取]' if is_selected else ''}"
        
        if st.button(btn_label, key=f"court_{name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            if is_selected:
                st.session_state.selected_court = None
            else:
                st.session_state.selected_court = name
                if st.session_state.selected_bench:
                    substitute(name, st.session_state.selected_bench)
            st.rerun()

# --- 替補席 ---
with col_bench:
    st.subheader(f"🪑 替補席 ({len(st.session_state.bench)}人)")
    for name, data in list(st.session_state.bench.items()):
        is_selected = (st.session_state.selected_bench == name)
        
        btn_label = f"⚪ {name}  |  總出賽: {format_time(data['total_sec'])} {' [已選取]' if is_selected else ''}"
        
        if st.button(btn_label, key=f"bench_{name}", use_container_width=True, type="primary" if is_selected else "secondary"):
            if is_selected:
                st.session_state.selected_bench = None
            else:
                st.session_state.selected_bench = name
                if st.session_state.selected_court:
                    substitute(st.session_state.selected_court, name)
            st.rerun()
