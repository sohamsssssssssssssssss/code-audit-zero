import streamlit as st
import redis
import os
import json
import time
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Cyber War: Code-Audit Zero", page_icon="⚔️", layout="wide")

# --- CUSTOM CSS (NEON CYBERPUNK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
    
    .stApp { background-color: #050505; color: #e0fbfc; font-family: 'Share Tech Mono', monospace; }
    
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 2px; }
    
    /* HUD Box Styling */
    .hud-box {
        background: rgba(10, 20, 30, 0.9);
        border: 2px solid #00f3ff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
        margin-bottom: 20px;
        text-align: center;
    }
    
    .judge-box {
        border-color: #ffd700;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
    }
    
    /* Agent Cards */
    .agent-card-red {
        border: 2px solid #ff0055;
        background: linear-gradient(180deg, rgba(50,0,0,0.8) 0%, rgba(0,0,0,0.9) 100%);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(255, 0, 85, 0.2);
    }
    
    .agent-card-blue {
        border: 2px solid #00bbff;
        background: linear-gradient(180deg, rgba(0,20,50,0.8) 0%, rgba(0,0,0,0.9) 100%);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 187, 255, 0.2);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background-color: #00ff41;
    }
    
    /* Terminal Logs */
    .terminal-box {
        background-color: #000;
        border: 1px solid #333;
        font-family: 'Share Tech Mono', monospace;
        padding: 10px;
        height: 300px;
        overflow-y: auto;
        font-size: 0.85rem;
        color: #0f0;
        text-shadow: 0 0 5px #0f0;
    }
    .log-red { color: #ff0055; text-shadow: 0 0 5px #ff0055; }
    .log-blue { color: #00bbff; text-shadow: 0 0 5px #00bbff; }
    .log-gold { color: #ffd700; text-shadow: 0 0 5px #ffd700; }
    
    .verdict-pass { color: #00ff41; font-weight: bold; font-size: 1.2rem; }
    .verdict-fail { color: #ff0055; font-weight: bold; font-size: 1.2rem; }
    
    </style>
    """, unsafe_allow_html=True)

# --- REDIS CONNECTION ---
redis_host = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

# --- SIDEBAR CONTROL ---
with st.sidebar:
    st.title("🎛️ CONTROL DECK")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 LAUNCH", type="primary", use_container_width=True):
            r.publish('commands', 'START_RED')
            st.toast("ATTACK SEQUENCE INITIATED", icon="⚔️")
    with col2:
        if st.button("♻️ RESET", use_container_width=True):
            r.publish('commands', 'RESET_ALL')
            r.delete('red_logs', 'blue_logs', 'z3_proof', 'exploits', 'KB_RED', 'KB_BLUE', 'PATCH_HISTORY', 'ATTACK_STATUS', 'JUDGE_VERDICT')
            st.toast("SYSTEM FLUSHED", icon="🧹")

    st.markdown("---")
    
    # Campaign Timer
    status = r.hgetall("ATTACK_STATUS")
    st.markdown("### ⏱️ MISSION CLOCK")
    if status:
        st.code(f"START: {status.get('start', '--:--')}\nEND:   {status.get('end', '--:--')}\nSTATE: {status.get('status', 'IDLE')}")
    else:
        st.code("NO ACTIVE MISSION")

# --- DATA FETCHING ---
def get_safe_json(key):
    try:
        data = r.get(key)
        return json.loads(data) if data else None
    except:
        return None

wallet = get_safe_json("app_wallet") or {"balance": 100}
vault = get_safe_json("app_vault") or {"admin_fund": 10000}
red_logs = r.lrange("red_logs", 0, -1)
blue_logs = r.lrange("blue_logs", 0, -1)
exploits = r.lrange("exploits", 0, -1)
patches = r.hgetall("PATCH_HISTORY")
verdict = get_safe_json("JUDGE_VERDICT")
kb_red = r.llen("KB_RED")
kb_blue = r.llen("KB_BLUE")

# --- SCORING LOGIC ---
# Red: 1 pt per $100 stolen + 50 pts per exploit
stolen = 10000 - vault.get("admin_fund", 10000)
red_score = (stolen // 100) + (len(exploits) * 50)

# Blue: 20 pts per block (implied) + 50 pts per patch + 100 per Z3 proof
# Estimate blocks: Total Red Logs - Successful exploits
total_red_actions = len([l for l in red_logs if "Reasoning" in l])
blocks = max(0, total_red_actions - len(exploits))
blue_score = (blocks * 20) + (len(patches) * 50)
if r.get("z3_proof"): blue_score += 100

# Health Logic
# Red Health: -10% per block
red_health = max(0, 100 - (blocks * 10))
# Blue Health: -20% per exploit
blue_health = max(0, 100 - (len(exploits) * 20))


# --- HEADER: THE JUDGE HUD ---
c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    st.markdown(f"""
    <div class="hud-box">
        <h3>🔴 RED TEAM</h3>
        <h2>{red_score} PTS</h2>
        <p>HEALTH: {red_health}%</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(red_health / 100)

with c2:
    if verdict:
        v_class = "verdict-pass" if verdict["status"] == "PASS" else "verdict-fail"
        v_msg = verdict["message"]
        v_status = verdict["status"]
    else:
        v_class = ""
        v_msg = "Awaiting Patch Deployment..."
        v_status = "ANALYZING"
        
    st.markdown(f"""
    <div class="hud-box judge-box">
        <h3>⚖️ GOLD AGENT (THE JUDGE)</h3>
        <h2 class="{v_class}">{v_status}</h2>
        <p>{v_msg}</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="hud-box">
        <h3>🔵 BLUE TEAM</h3>
        <h2>{blue_score} PTS</h2>
        <p>HEALTH: {blue_health}%</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(blue_health / 100)


# --- BATTLE ARENA ---
st.markdown("<br>", unsafe_allow_html=True)
col_red, col_blue = st.columns(2)

with col_red:
    st.markdown('<div class="agent-card-red">', unsafe_allow_html=True)
    st.markdown("### 👺 ATTACKER (RED)")
    
    st.markdown(f"**💰 MONEY STOLEN:** ${stolen}")
    st.markdown(f"**🧠 TACTICS LEARNED:** {kb_red}")
    
    st.markdown("#### 📟 LIVE FEED")
    # Show last 5 logs with HTML styling
    logs_html = "<br>".join([f"<span class='log-red'>{l}</span>" for l in red_logs[:8]])
    st.markdown(f'<div class="terminal-box">{logs_html}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_blue:
    st.markdown('<div class="agent-card-blue">', unsafe_allow_html=True)
    st.markdown("### 🛡️ DEFENDER (BLUE)")
    
    st.markdown(f"**🧱 ATTACKS BLOCKED:** {blocks}")
    st.markdown(f"**🔧 PATCHES APPLIED:** {len(patches)}")
    
    if r.get("z3_proof"):
        st.success("🏆 FORMAL PROOF VERIFIED")
    
    st.markdown("#### 📟 LIVE FEED")
    logs_html = "<br>".join([f"<span class='log-blue'>{l}</span>" for l in blue_logs[:8]])
    st.markdown(f'<div class="terminal-box">{logs_html}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- REFRESH ---
time.sleep(2)
st.rerun()