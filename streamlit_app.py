#!/usr/bin/env python3
"""
Poly Monitor — 과제 제출용 (테스트 데이터 버전)
리스트, 조건문, 반복문 사용
"""
 
import streamlit as st
import time
import psutil
import random
 
# ─── 설정값 ────────────────────────────────────────────────
REFRESH_INTERVAL = 2
WARN_PCT         = 75
DANGER_PCT       = 90
HISTORY_MAX      = 20
 
VRAM_BYTES_PER_FACE = 100
RAM_BYTES_PER_FACE  = 300
VRAM_BUDGET_RATIO   = 0.35
RAM_BUDGET_RATIO    = 0.25
 
# 경고 단계 정의 (리스트)
WARNING_LEVELS = [
    {"label": "정상", "min": 0,          "max": WARN_PCT,   "color": "normal",  "icon": "✅"},
    {"label": "주의", "min": WARN_PCT,   "max": DANGER_PCT, "color": "warning", "icon": "⚠️"},
    {"label": "위험", "min": DANGER_PCT, "max": 999,        "color": "error",   "icon": "🚨"},
]
 
# ══════════════════════════════════════════════════════════
#  시스템 정보 수집
# ══════════════════════════════════════════════════════════
 
def _try_gputil():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return gpus[0].memoryTotal, gpus[0].name
    except Exception:
        pass
    return None, None
 
def get_system_info():
    ram_mb = psutil.virtual_memory().total / (1024 ** 2)
    vram_mb, gpu_name = _try_gputil()
    return {
        "ram_mb":   ram_mb,
        "vram_mb":  vram_mb,
        "gpu_name": gpu_name or "GPU 정보 감지 불가",
    }
 
def calc_safe_max(info):
    # 리스트에 후보 한계값 수집 후 min() 적용
    candidates = []
    if info["vram_mb"]:
        candidates.append(
            int(info["vram_mb"] * VRAM_BUDGET_RATIO * 1024 * 1024 / VRAM_BYTES_PER_FACE)
        )
    candidates.append(
        int(info["ram_mb"] * RAM_BUDGET_RATIO * 1024 * 1024 / RAM_BYTES_PER_FACE)
    )
    return min(candidates)
 
# ══════════════════════════════════════════════════════════
#  테스트용 면 수 시뮬레이션 (Maya 대체)
# ══════════════════════════════════════════════════════════
 
def get_face_count(safe_max: int) -> tuple:
    """
    슬라이더 값 기반으로 면 수 반환
    반복문으로 단계별 mesh 면 수 합산 시뮬레이션
    """
    base = st.session_state.get("face_input", 1_000_000)
 
    # 반복문: mesh 5개의 면 수를 리스트로 구성 후 합산
    mesh_counts = []
    for i in range(5):                         # 반복문
        ratio = [0.35, 0.25, 0.20, 0.12, 0.08][i]
        mesh_counts.append(int(base * ratio))
 
    total = sum(mesh_counts)                   # 리스트 합산
    return total, mesh_counts
 
# ══════════════════════════════════════════════════════════
#  경고 단계 판별
# ══════════════════════════════════════════════════════════
 
def get_level(pct: float) -> dict:
    for level in WARNING_LEVELS:               # 반복문
        if level["min"] <= pct < level["max"]: # 조건문
            return level
    return WARNING_LEVELS[-1]
 
def get_warning_messages(pct: float, count: int) -> list:
    messages = []
 
    if pct >= WARN_PCT:                        # 조건문
        messages.append(f"현재 {count:,} 면 — 안전 한계의 {pct:.1f}% 사용 중")
 
    if pct >= DANGER_PCT:                      # 조건문
        messages.append("즉시 폴리 수를 줄이거나 씬을 분할하세요")
        messages.append("뷰포트 크래시가 발생할 수 있습니다")
    elif pct >= WARN_PCT:                      # 조건문
        messages.append("폴리 수 감소 또는 LOD 적용을 검토하세요")
 
    return messages
 
# ══════════════════════════════════════════════════════════
#  히스토리 관리
# ══════════════════════════════════════════════════════════
 
def update_history(history: list, count: int) -> list:
    history.append(count)
    if len(history) > HISTORY_MAX:             # 조건문
        history = history[-HISTORY_MAX:]
    return history
 
# ══════════════════════════════════════════════════════════
#  UI 렌더링 함수
# ══════════════════════════════════════════════════════════
 
def render_spec_table(info: dict, safe_max: int):
    rows = [                                   # 리스트
        ("GPU",      info["gpu_name"]),
        ("VRAM",     f'{info["vram_mb"]:.0f} MB' if info["vram_mb"] else "감지 불가"),
        ("RAM",      f'{info["ram_mb"]:.0f} MB'),
        ("안전 최대", f'{safe_max:,} 면'),
    ]
    cols = st.columns(len(rows))
    for col, (label, value) in zip(cols, rows): # 반복문
        col.metric(label, value)
 
def render_mesh_table(mesh_counts: list):
    st.caption("📦 Mesh별 면 수 분석")
    mesh_names = ["Mesh_Body", "Mesh_Head", "Mesh_Cloth", "Mesh_Hair", "Mesh_Prop"]
    for i in range(len(mesh_counts)):          # 반복문
        col1, col2 = st.columns([2, 3])
        col1.text(mesh_names[i])
        col2.text(f"{mesh_counts[i]:,} 면")
 
def render_warnings(messages: list, level: dict):
    if not messages:                           # 조건문
        return
    for msg in messages:                       # 반복문
        if level["color"] == "error":          # 조건문
            st.error(f'{level["icon"]} {msg}')
        elif level["color"] == "warning":      # 조건문
            st.warning(f'{level["icon"]} {msg}')
 
def render_history_chart(history: list):
    if len(history) < 2:                       # 조건문
        st.caption("데이터 수집 중...")
        return
    import pandas as pd
    chart_data = [{"면 수": v} for v in history]  # 리스트 컴프리헨션
    st.line_chart(pd.DataFrame(chart_data))
 
# ══════════════════════════════════════════════════════════
#  메인
# ══════════════════════════════════════════════════════════
 
def main():
    st.set_page_config(page_title="Poly Monitor", page_icon="🎛", layout="centered")
 
    st.title("🎛 Poly Monitor")
    st.caption("3D 모델링 폴리곤 면 수 모니터 — 컴퓨터 사양 기반 안전 한계 경고")
 
    # 세션 초기화
    if "initialized" not in st.session_state:
        st.session_state.info        = get_system_info()
        st.session_state.safe_max    = calc_safe_max(st.session_state.info)
        st.session_state.history     = []
        st.session_state.face_input  = 1_000_000
        st.session_state.initialized = True
 
    info     = st.session_state.info
    safe_max = st.session_state.safe_max
 
    # ── 시스템 사양 ──
    st.subheader("💻 시스템 사양")
    render_spec_table(info, safe_max)
    st.divider()
 
    # ── 면 수 입력 슬라이더 ──
    st.subheader("🎚️ 면 수 입력")
    st.session_state.face_input = st.slider(
        "씬의 총 면 수 설정",
        min_value=0,
        max_value=safe_max * 2,
        value=st.session_state.face_input,
        step=100_000,
        format="%d 면"
    )
 
    # ── 면 수 계산 ──
    count, mesh_counts = get_face_count(safe_max)
    pct   = min(count / safe_max * 100, 100) if safe_max > 0 else 0
    level = get_level(pct)
 
    # ── 현재 수치 ──
    st.subheader("📐 현재 씬 면 수")
    col1, col2 = st.columns(2)
    col1.metric("총 면 수",  f"{count:,}")
    col2.metric("사용률",    f"{pct:.1f} %",
                delta=f'{level["icon"]} {level["label"]}')
 
    st.progress(min(pct / 100, 1.0))
 
    # 단계 기준 안내 (리스트 반복)
    st.caption("단계 기준:")
    level_cols = st.columns(len(WARNING_LEVELS))
    for col, lv in zip(level_cols, WARNING_LEVELS):  # 반복문
        col.caption(f'{lv["icon"]} {lv["label"]} (< {lv["max"]}%)')
 
    st.divider()
 
    # ── Mesh별 상세 ──
    render_mesh_table(mesh_counts)
    st.divider()
 
    # ── 경고 메시지 ──
    messages = get_warning_messages(pct, count)
    render_warnings(messages, level)
 
    # ── 히스토리 차트 ──
    st.subheader("📈 면 수 변화 추이")
    st.session_state.history = update_history(st.session_state.history, count)
    render_history_chart(st.session_state.history)
 
    # ── 하단 정보 ──
    st.divider()
    info_items = [                             # 리스트
        f"갱신 간격: {REFRESH_INTERVAL}초",
        f"경고 임계: {WARN_PCT}%",
        f"위험 임계: {DANGER_PCT}%",
        f"기록 보관: 최근 {HISTORY_MAX}회",
    ]
    st.caption("  |  ".join(info_items))
 
    # ── 자동 갱신 ──
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
 
 
if __name__ == "__main__":
    main()
 