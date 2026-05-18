# main file

import streamlit as st
import torch
import hashlib
import math
import time
import datetime
import pandas as pd
import difflib 
import json      
import os        
from transformers import AutoTokenizer, AutoModelForCausalLM

# ==========================================
# 🎨 UI CONFIGURATION & GLASS CSS
# ==========================================
st.set_page_config(
    page_title="Watermark AI Studio",
    page_icon="🕵️‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Safe Glassmorphism CSS
st.markdown("""
<style>
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3em; 
        background-color: #FF4B4B; color: white; font-weight: bold; border: none; 
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #ff3333; box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    
    .metric-container { 
        background: rgba(150, 150, 150, 0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        padding: 15px; border-radius: 12px; border: 1px solid rgba(150, 150, 150, 0.2);
        border-left: 5px solid #FF4B4B; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .metadata-box { 
        font-size: 0.85em; background: rgba(150, 150, 150, 0.05); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid rgba(150, 150, 150, 0.2); box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }

    .verify-success { 
        padding: 1rem; border-radius: 12px; margin-top: 10px; background: rgba(16, 185, 129, 0.15); 
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(16, 185, 129, 0.4); box-shadow: 0 8px 32px rgba(16, 185, 129, 0.1);
    }
    .verify-warning { 
        padding: 1rem; border-radius: 12px; margin-top: 10px; background: rgba(245, 158, 11, 0.15); 
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(245, 158, 11, 0.4); box-shadow: 0 8px 32px rgba(245, 158, 11, 0.1);
    }
    .verify-fail { 
        padding: 1rem; border-radius: 12px; margin-top: 10px; background: rgba(239, 68, 68, 0.15); 
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(239, 68, 68, 0.4); box-shadow: 0 8px 32px rgba(239, 68, 68, 0.1);
    }
    .database-match { 
        padding: 1rem; border-radius: 12px; margin-top: 15px; font-size: 0.9em; background: rgba(14, 165, 233, 0.15); 
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(14, 165, 233, 0.4); box-shadow: 0 8px 32px rgba(14, 165, 233, 0.1);
    }
    
    .verify-success h3, .verify-warning h3, .verify-fail h3, .database-match h4 { margin-top: 0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 PERSISTENT DATABASE LOGIC
# ==========================================
HISTORY_FILE = "watermark_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

if 'generation_history' not in st.session_state:
    st.session_state.generation_history = load_history()

# ==========================================
# ⚙️ MODEL LOADER (Cached)
# ==========================================
MODEL_PATH = "./saved_qwen_1.5b" 
FALLBACK_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

@st.cache_resource
def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    target_path = MODEL_PATH
    try:
        if not os.path.exists(target_path):
            target_path = FALLBACK_MODEL
        tokenizer = AutoTokenizer.from_pretrained(target_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(target_path, torch_dtype="auto", device_map=device, trust_remote_code=True)
        return tokenizer, model, device, target_path
    except Exception as e:
        return None, None, str(e), target_path

with st.spinner("Loading AI Model... (this happens once)"):
    tokenizer, model, device, active_model_name = load_model()

if isinstance(device, str) and "error" in device.lower():
    st.error(f"Failed to load model: {device}")
    st.stop()

# ==========================================
# 🧠 WATERMARK LOGIC
# ==========================================
hash_cache = {}

def get_token_bit(token_id, secret_key):
    cache_key = f"{token_id}-{secret_key}"
    if cache_key in hash_cache: return hash_cache[cache_key]
    h = hashlib.sha256(f"{token_id}{secret_key}".encode()).hexdigest()
    bit = int(h, 16) % 2
    print("token : ",bit , "\n")
    hash_cache[cache_key] = bit
    return bit

def calculate_entropy(probs):
    return -torch.sum(probs * torch.log(probs + 1e-9)).item()

# ==========================================
# 🖥️ SIDEBAR CONTROLS 
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("🔑 Watermark Keys", expanded=True):
        secret_key = st.text_input("Secret Key", "my_secret_key_2025", type="password")
        watermark_bits = st.text_input("Binary Pattern", "101011")
        
        combined_key = f"{secret_key}{watermark_bits}"
        hashed_key = hashlib.sha256(combined_key.encode()).hexdigest()
        st.text_input("Hashed Key (SHA-256)", hashed_key, disabled=True)
    
    with st.expander("🛡️ Strength Controls", expanded=False):
        watermark_prob = st.slider("Watermark Probability", 0.0, 1.0, 1.0)
        bit_interval = st.number_input("Token Interval", min_value=1, value=1)
        entropy_threshold = st.number_input("Entropy Threshold", value=0.0, step=0.1)
        min_prefix = st.number_input("Safe Prefix Length", value=0)
    
    with st.expander("🤖 Model Params", expanded=False):
        max_tokens = st.slider("Max New Tokens", 50, 500, 200)
        temperature = st.slider("Temperature", 0.1, 1.5, 0.7)

    st.divider()
    st.caption(f"💾 Database Records: {len(st.session_state.generation_history)}")

# ==========================================
# 🚀 MAIN APP LOGIC
# ==========================================
st.title("🕵️‍♀️ Watermark AI Studio")
st.markdown("Generate text with an invisible binary signature embedded in the word choices.")

tab1, tab2 = st.tabs(["📝 Generate & Embed", "🔍 Verify & Detect"])

# --- TAB 1: GENERATION ---
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        prompt = st.text_area("Enter your prompt:", "Why are watermelons good for you?", height=150)
        generate_btn = st.button("🚀 Generate Response")

    if generate_btn and prompt:
        messages = [{"role": "user", "content": prompt}]
        text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        input_ids = tokenizer.encode(text_input, return_tensors="pt").to(device)
        
        payload = (watermark_bits * 1000)
        generated_ids = []
        token_log = []
        past_key_values = None
        current_input = input_ids

        output_box = st.empty()
        start_time = time.time()
        full_text = ""
        progress_bar = st.progress(0)
        
        for i in range(max_tokens):
            with torch.inference_mode():
                out = model(current_input, past_key_values=past_key_values, use_cache=True)
            
            past_key_values = out.past_key_values
            logits = out.logits[:, -1, :].clone()

            for t in set(generated_ids[-50:]): logits[0, t] /= 1.2

            top_vals, top_ids = torch.topk(logits, 100) 
            probs = torch.softmax(top_vals / temperature, dim=-1)
            entropy = calculate_entropy(probs)

            use_watermark = (i >= min_prefix and i % bit_interval == 0 and entropy > entropy_threshold and torch.rand(1).item() < watermark_prob)

            target_bit = None
            forced = False
            
            if use_watermark:
                bit_index = (i // bit_interval) % len(watermark_bits)
                target_bit = int(payload[bit_index])
                
                valid_ids, valid_probs = [], []
                for idx, t_id in enumerate(top_ids[0]):
                    if get_token_bit(t_id.item(), secret_key) == target_bit:
                        valid_ids.append(t_id.item())
                        valid_probs.append(probs[0, idx].item())
                
                if valid_ids:
                    probs_tensor = torch.tensor(valid_probs)
                    probs_tensor /= probs_tensor.sum()
                    next_token = valid_ids[torch.multinomial(probs_tensor, 1).item()]
                    forced = True
                else:
                    next_token = top_ids[0][torch.multinomial(probs[0], 1)].item()
                    forced = False 
            else:
                next_token = top_ids[0][torch.multinomial(probs[0], 1)].item()

            generated_ids.append(next_token)
            current_input = torch.tensor([[next_token]], device=device)
            
            token_str = tokenizer.decode([next_token])
            full_text += token_str
            
            token_log.append({
                "Token": token_str,
                "Bit ID": get_token_bit(next_token, secret_key),
                "Status": "FORCED" if forced else "Natural",
                "Target": target_bit if target_bit is not None else "-"
            })
            
            output_box.markdown(f"**Generating:**\n\n{full_text} ...")
            progress_bar.progress(min((i + 1) / max_tokens, 1.0))

            if next_token == tokenizer.eos_token_id:
                break

        elapsed = time.time() - start_time
        speed = len(generated_ids) / elapsed
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        progress_bar.empty()
        output_box.markdown("### 🤖 Final Response")
        st.success(full_text)
        
        # SAVE TO MEMORY FOR VERIFICATION
        new_record = {
            "text": full_text.strip(),
            "model": active_model_name,
            "timestamp": current_time_str,
            "latency": f"{elapsed:.2f} seconds",
            "speed": f"{speed:.2f} t/s",
            "hash": hashed_key[:24],
            "tokens": len(generated_ids)
        }
        st.session_state.generation_history.append(new_record)
        save_history(st.session_state.generation_history)

        st.markdown(f"""
        <div class='metadata-box'>
            <b>🧾 Generation Metadata (Saved to Database)</b><br>
            <b>Model Source:</b> {active_model_name}<br>
            <b>Generated On:</b> {current_time_str}<br>
            <b>Hardware:</b> {device.upper()}<br>
            <b>Latency:</b> {elapsed:.2f} seconds ({speed:.2f} tokens/sec)<br>
            <b>Watermark Hash (SHA-256):</b> <code>{hashed_key[:24]}...</code>
        </div>
        """, unsafe_allow_html=True)
        
        with col2:
            forced_count = sum(1 for x in token_log if x['Status']=='FORCED')
            rate = (forced_count/len(token_log)*100) if token_log else 0
            
            st.markdown(f"""
            <div class='metric-container'>
                <h4>📊 Stats</h4>
                <b>Speed:</b> {speed:.2f} t/s<br>
                <b>Total Tokens:</b> {len(generated_ids)}<br>
                <b>Forced Tokens:</b> {forced_count}<br>
                <b>Watermark Rate:</b> {rate:.1f}%
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🕵️ Token Debugger")
        df_log = pd.DataFrame(token_log)
        def highlight_forced(row):
            if row['Status'] == 'FORCED':
                return ['background-color: rgba(16, 185, 129, 0.2); color: #065f46'] * len(row)
            return [''] * len(row)
        st.dataframe(df_log.style.apply(highlight_forced, axis=1), use_container_width=True, height=400)

# --- TAB 2: VERIFICATION ---
with tab2:
    st.markdown("### 🧬 Verify AI Generation")
    st.info("Paste text below. The verifier will check the mathematical watermark and cross-reference our local JSON database.")
    
    verify_text = st.text_area("Paste text here:", height=150)
    check_btn = st.button("🔍 Analyze Text")

    if check_btn and verify_text:
        
        # ----------------------------------------------------
        # 🧹 NORMALIZATION: Fix invisible browser formatting
        # ----------------------------------------------------
        # Convert carriage returns to standard newlines and strip edge spaces
        normalized_math_text = verify_text.replace('\r\n', '\n').strip()
        
        token_ids = tokenizer.encode(normalized_math_text, add_special_tokens=False)
        
        if len(token_ids) < 15:
            st.warning("⚠️ Text is too short for reliable detection (need >15 tokens).")
        else:
            # 1. Z-SCORE MATH CHECK
            best_z_score = -999
            best_offset = 0
            best_match_rate = 0
            
            pattern = [int(b) for b in watermark_bits]
            pattern_len = len(pattern)
            
            for offset in range(pattern_len):
                matches = 0
                valid_tokens = 0
                
                for i, t_id in enumerate(token_ids):
                    expected_bit = pattern[(i + offset) % pattern_len]
                    actual_bit = get_token_bit(t_id, secret_key)
                    
                    if actual_bit == expected_bit:
                        matches += 1
                    valid_tokens += 1
                
                if valid_tokens > 0:
                    match_rate = matches / valid_tokens
                    z = (match_rate - 0.5) / math.sqrt((0.5 * 0.5) / valid_tokens)
                    
                    if z > best_z_score:
                        best_z_score = z
                        best_offset = offset
                        best_match_rate = match_rate

            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Token Count", len(token_ids))
            c2.metric("Pattern Match Rate", f"{best_match_rate*100:.1f}%")
            c3.metric("Z-Score (Confidence)", f"{best_z_score:.2f}")
            
            # Visual Gauge
            st.markdown("**Confidence Gauge (Z-Score)**")
            gauge_val = min(max(best_z_score, 0.0), 8.0) / 8.0
            st.progress(gauge_val)
            
            # 2. DATABASE CROSS-REFERENCE (Whitespace blind)
            best_sim = 0.0
            best_meta = None
            
            # Remove ALL extra whitespace/newlines for a pure text comparison
            verify_clean_db = " ".join(verify_text.split())
            
            for record in st.session_state.generation_history:
                record_clean_db = " ".join(record["text"].split())
                sim = difflib.SequenceMatcher(None, verify_clean_db, record_clean_db).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_meta = record
            
            st.divider()
            
            # 3. GRANULAR BANNERS
            if best_z_score >= 5.0 and best_match_rate >= 0.80:
                st.markdown(f"""
                <div class="verify-success">
                    <h3>✅ PRISTINE AI (Unedited)</h3>
                    <p><strong>Very Strong Signal:</strong> The text follows the watermark pattern almost perfectly. It was likely copy-pasted directly from the AI with zero or minimal human edits.</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

            elif best_z_score >= 3.5:
                st.markdown(f"""
                <div class="verify-success">
                    <h3>✅ VERIFIED AI (Slightly Edited)</h3>
                    <p><strong>Strong Signal:</strong> A clear watermark is present, but the match rate is slightly fragmented. This usually happens when a human makes minor edits, tweaks formatting, or if the AI skipped watermarking on highly confident words.</p>
                </div>
                """, unsafe_allow_html=True)

            elif best_z_score >= 2.0:
                st.markdown(f"""
                <div class="verify-warning">
                    <h3>⚠️ LIKELY AI (Heavily Edited or Mixed)</h3>
                    <p><strong>Moderate Signal:</strong> A residual trace of the watermark pattern was found. The text has likely been heavily rewritten/paraphrased by a human, or it is a mix of human-written and AI-generated paragraphs.</p>
                </div>
                """, unsafe_allow_html=True)

            elif best_z_score >= 1.0:
                st.markdown(f"""
                <div class="verify-warning">
                    <h3>🕵️ INCONCLUSIVE / SUSPICIOUS</h3>
                    <p><strong>Weak Signal:</strong> The pattern match is only slightly above random chance. This could be a pure coincidence, or it might contain a very tiny fragment of AI text hidden inside a human document.</p>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class="verify-fail">
                    <h3>❌ HUMAN-WRITTEN (Unwatermarked)</h3>
                    <p><strong>No Signal:</strong> The text matches random chance (~50%). There is no statistical evidence of the hidden pattern.</p>
                </div>
                """, unsafe_allow_html=True)

            # 4. SHOW METADATA IF FOUND IN JSON MEMORY
            if best_meta and best_sim > 0.40:
                match_type = "Exact Match" if best_sim > 0.98 else f"Partial Match ({best_sim*100:.1f}% similar)"
                st.markdown(f"""
                <div class='database-match'>
                    <h4>🗄️ Database Record Found: {match_type}</h4>
                    <p>We found the original record for this text in the local <code>watermark_history.json</code> file!</p>
                    <ul>
                        <li><b>Original Generation Date:</b> {best_meta['timestamp']}</li>
                        <li><b>Model Used:</b> {best_meta['model']}</li>
                        <li><b>Original Token Count:</b> {best_meta['tokens']}</li>
                        <li><b>Watermark Hash:</b> <code>{best_meta['hash']}...</code></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)