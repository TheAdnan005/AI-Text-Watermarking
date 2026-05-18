# AI-Text-Watermarking
# 🕵️‍♀️ Watermark AI Studio

AI Text Watermarking system for Large Language Models (LLMs) that embeds invisible binary watermarks into generated text for authenticity verification, ownership protection, and tamper detection.

Built using Streamlit, PyTorch, and Hugging Face Transformers.

---

## 🚀 Features

- 🔐 Invisible probabilistic text watermarking
- 🧠 Black-box watermark embedding (no retraining required)
- 📊 Token-level watermark analysis
- 🧬 Statistical watermark verification using Z-score detection
- 🛡️ Ownership verification & tamper detection
- 💾 Persistent local watermark history database
- ⚡ Real-time token generation debugger
- 🎨 Modern glassmorphism Streamlit UI
- 🤖 Works with Qwen models and Hugging Face models

---

## 🏗️ Architecture

The system uses a dual-layer watermarking approach:

### 1️⃣ Token-Level Probabilistic Watermarking
- Uses SHA-256 hashing on token IDs
- Maps tokens into binary watermark bits
- Selects tokens matching the target watermark pattern during generation

### 2️⃣ Statistical Verification Engine
- Performs pattern matching on generated tokens
- Uses Z-score analysis for watermark confidence detection
- Detects:
  - Unedited AI text
  - Slightly edited AI text
  - Heavily paraphrased AI text
  - Human-written text

---

## 📦 Tech Stack

- Python
- Streamlit
- PyTorch
- Hugging Face Transformers
- Qwen LLM
- Pandas

---

## 📂 Project Structure

```bash
├── app.py
├── requirements.txt
├── watermark_history.json
├── saved_qwen_1.5b/
└── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone <your-repo-url>
cd watermark-ai-studio
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### 3️⃣ Activate Environment

#### Windows
```bash
venv\Scripts\activate
```

#### Linux / Mac
```bash
source venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run Application

```bash
streamlit run app.py
```

---

## 🤖 Model Setup

The application supports:

- Local Qwen model
- Hugging Face fallback model

Default configuration:

```python
MODEL_PATH = "./saved_qwen_1.5b"
FALLBACK_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
```

Place your downloaded model inside:

```bash
./saved_qwen_1.5b
```

If unavailable, the system automatically downloads the fallback model.

---

## 🔍 Watermark Verification

The verifier checks:

- Pattern match rate
- Statistical confidence (Z-score)
- Local database similarity
- Tampering evidence

### Detection Levels

| Z-Score | Result |
|---|---|
| >= 5.0 | Pristine AI |
| >= 3.5 | Verified AI |
| >= 2.0 | Likely AI |
| >= 1.0 | Inconclusive |
| < 1.0 | Human Written |

---

## 📊 Example Use Cases

- AI content authenticity verification
- LLM ownership protection
- AI-generated text tracking
- Content tamper detection
- Academic AI disclosure systems
- Enterprise AI security pipelines

---

## 🛡️ Security Notes

- No model retraining required
- Works in black-box environments
- Watermarks are invisible to users
- Resistant to minor paraphrasing
- Maintains text fluency and coherence

---

## 📸 UI Features

- Live token debugger
- Watermark statistics
- Real-time generation tracking
- Persistent generation history
- Interactive verification dashboard

---

## 📜 License

This project is for educational and research purposes.

---

## 👨‍💻 Author

Developed as an AI Security & Watermarking research project.
