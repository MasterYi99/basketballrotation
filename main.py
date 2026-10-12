import streamlit as st
import time

st.set_page_config(page_title="籃球輪替與即時管理系統", layout="wide")

# 1. 預設名單
DEFAULT_ROSTER_TEXT = """Aaron SG
宗哥 PG
冠傑 PG
智翔 SF
哲翊 SF
小梁 SG
秋偉 SF
逸豐 C
阿勛 SG
本三 SF
國城 SF
禹豪 C
邱 PG
書辰 SG
Wang SG
林序 PF
威良 SF
姆斯 PF
倫哥 SF"""

# 2. 初始化與重置函式
def init_game(roster_list, reset_lineup=True):
    st.session_state.game_running = False
    st.session_state.selected_court = None
    st.session_state.selected_bench = None

    if reset_lineup:
        # 前 5 位先發，其餘替補
        st.session_state.on_court = {
            name: {"total_sec": 0, "in_time": None} for name in roster_list[:5]
        }
        st.session_state.bench = {
            name: {"total_sec": 0, "in_time": None} for name in roster_list[5:]
        }
    else:
        # 保留現有狀態，移除不在名單中的人，新增新進人員
        existing_court = st.session_state.get("on_court", {})
        existing_bench = st.session_state.get("bench", {})
        
        new_court = {}
        new_bench = {}
        
        # 優先保留場上人員（最多前5位）
        for name in roster_list:
            if name in existing_court and len(new_court) < 5:
                new_court[name] = existing_court[name]
                new_court[name]["in_time"] = None  # 編輯後先暫停
            elif name in existing_bench:
                new_bench[name] = existing_bench[name]
            else:
                # 新增的球員
                if len(new_court) < 5:
                    new_court[name] = {"total_sec": 0, "in_time": None}
                else:
                    new_bench[name] = {"total_sec": 0, "in_time": None}
                    
        st.session_state.on_court = new_court
        st.session_state.bench = new_bench

# 3. 初始狀態建立
if "roster_text" not in st.session_state:
    st.session_state.roster_text = DEFAULT_ROSTER_TEXT

if "on_court" not in st.session_state:
    roster = [line.strip() for line in st.session_state.roster_text.split("\n") if line.strip()]
    init_game(roster, reset_lineup=True)

# 4. 工具函式
def format_time(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"

def get_current_time(player_data):
    if st.session_state.game_running and player_data["in_time"] is not None:
        elapsed = time.time() - player_data["in_time"]
        return player_data["total_sec"] + elapsed
    return player_data["total_sec"]

def toggle_game():
    now = time.time()
    if st.session_state.game_running:
        for data in st.session_state.on_court.values():
            if data["in_time"] is not None:
                data["total_sec"] += (now - data["in_time"])
                data["in_time"] = None
        st.session_state.game_running = False
    else:
        for data in st.session_state.on_court.values():
            data["in_time"] = now
        st.session_state.game_running = True

def substitute(court_player, bench_player):
    now = time.time()
    # 換下
    c_data = st.session_state.on_court.pop(court_player)
    if st.session_state.game_running and c_data["in_time"] is not None:
        c_data["total_sec"] += (now - c_data["in_time"])
    c_data["in_time"] = None
    st.session_state.bench[court_player] = c_data

    # 換上
    b_data = st.session_state.bench.pop(bench_player)
    b_data["in_time"] = now if st.session_state.game_running else None
    st.session_state.on_court[bench_player] = b_data

    st.session_state.selected_court = None
    st.session_state.selected_bench = None

# --- 側邊欄：線上編輯名單 ---
with st.sidebar:
    st.header("⚙️ 球員名單編輯")
    st.caption("一行一位球員，前 5 位將作為預設先發陣容。")
    
    new_text = st.text_area(
        "編輯名單內容：",
        value=st.session_state.roster_text,
        height=380
    )
    
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        if st.button("💾 更新名單", use_container_width=True, type="primary"):
            st.session_state.roster_text = new_text
            cleaned_roster = [line.strip() for line in new_text.split("\n") if line.strip()]
            # 更新名單，保留已出賽球員的秒數
            init_game(cleaned_roster, reset_lineup=False)
            st.success("名單已同步更新！")
            st.rerun()

    with col_up2:
        if st.button("🔄 復原預設", use_container_width=True):
            st.session_state.roster_text = DEFAULT_ROSTER_TEXT
            cleaned_roster = [line.strip() for line in DEFAULT_ROSTER_TEXT.split("\n") if line.strip()]
            init_game(cleaned_roster, reset_lineup=True)
            st.rerun()

# --- 主畫面頂部控制面板 ---
st.title("🏀 籃球輪替與上場時間管理")

ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])

with ctrl1:
    status_icon = "🟢 比賽進行中 (每秒自動跳秒)" if st.session_state.game_running else "🔴 暫停中"
    st.markdown(f"### 狀態：{status_icon}")

with ctrl2:
    if st.button("▶️ 開始計時" if not st.session_state.game_running else "⏸️ 暫停計時", use_container_width=True, type="primary"):
        toggle_game()
        st.rerun()

with ctrl3:
    @st.dialog("⚠️ 計時重置確認")
    def confirm_reset_dialog():
        st.write("請選擇要執行的操作：")
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("⏱️ 僅時間歸零", use_container_width=True, help="保留目前場上名單，時間全部重置為 00:00"):
                for data in st.session_state.on_court.values():
                    data["total_sec"] = 0
                    data["in_time"] = None
                for data in st.session_state.bench.values():
                    data["total_sec"] = 0
                    data["in_time"] = None
                st.session_state.game_running = False
                st.rerun()
        with btn_c2:
            if st.button("🚨 全場重置", use_container_width=True, help="時間歸零，並恢復至前 5 人先發"):
                cleaned_roster = [line.strip() for line in st.session_state.roster_text.split("\n") if line.strip()]
                init_game(cleaned_roster, reset_lineup=True)
                st.rerun()

    if st.button("⏹️ 重置 / 歸零", use_container_width=True):
        confirm_reset_dialog()

# 選取提示
c_sel = st.session_state.selected_court
b_sel = st.session_state.selected_bench
if c_sel and not b_sel:
    st.info(f"👉 已選取場上球員：**{c_sel}**，請點選要換上的替補球員。")
elif b_sel and not c_sel:
    st.info(f"👉 已選取替補球員：**{b_sel}**，請點選要換下的場上球員。")
else:
    st.caption("💡 提示：點擊一名「場上球員」與一名「替補球員」即可完成輪替；可在側邊欄隨時編輯球員。")

st.divider()

# --- 球員卡片渲染 (自動跳秒) ---
run_interval = "1s" if st.session_state.game_running else None

@st.fragment(run_every=run_interval)
def render_roster():
    col_court, col_bench = st.columns(2)

    # 1. 場上球員
    with col_court:
        st.subheader(f"⚡ 場上球員 ({len(st.session_state.on_court)}/5)")
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

    # 2. 替補席
    with col_bench:
        st.subheader(f"🪑 替補席 ({len(st.session_state.bench)}人)")
        for name, data in list(st.session_state.bench.items()):
            is_selected = (st.session_state.selected_bench == name)
            
            btn_label = f"⚪ {name}  |  出賽: {format_time(data['total_sec'])} {' [已選取]' if is_selected else ''}"
            
            if st.button(btn_label, key=f"bench_{name}", use_container_width=True, type="primary" if is_selected else "secondary"):
                if is_selected:
                    st.session_state.selected_bench = None
                else:
                    st.session_state.selected_bench = name
                    if st.session_state.selected_court:
                        substitute(st.session_state.selected_court, name)
                st.rerun()

render_roster()
