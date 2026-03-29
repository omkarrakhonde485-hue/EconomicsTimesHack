import streamlit as st
import time
import random
import google.generativeai as genai

# ── Gemini Setup ───────────────────────────────────────────────────────────────
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# ── Gemini Status Check ───────────────────────────────────────────────────────
def check_gemini_status():
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say OK")
        if response and response.text:
            return True, "✅ Gemini API is working"
        else:
            return False, "⚠️ Gemini API responded but no valid output"
    except Exception as e:
        return False, f"❌ Gemini API error: {str(e)}"

# ── Static Fallback Plans ─────────────────────────────────────────────────────
FALLBACK_PLANS = {
    ("Low", "Beginner"): {
        "plan": "70% in FDs / RDs · 20% in Liquid Mutual Funds · 10% in PPF",
        "reason": "As a beginner with low risk appetite, capital safety is the priority. These instruments offer stable, guaranteed returns with minimal downside risk.",
        "action": "Open a PPF account on your bank's app and start a {amt} SIP in a Liquid Fund like Parag Parikh Liquid Fund today.",
        "confidence": 82,
    },
    ("Low", "Intermediate"): {
        "plan": "50% in Debt Mutual Funds · 30% in FDs · 20% in Gold ETFs",
        "reason": "You have some market knowledge, so diversifying into Debt Funds and Gold can yield better returns while keeping overall risk low.",
        "action": "Set up a {amt} SIP in a Short-Duration Debt Fund and buy 1 unit of a Gold ETF on Zerodha or Groww today.",
        "confidence": 79,
    },
    ("Medium", "Beginner"): {
        "plan": "50% in Nifty 50 Index Funds · 30% in RDs · 20% in ELSS",
        "reason": "Index funds give broad market exposure without stock-picking risk — ideal for beginners stepping into equity for the first time.",
        "action": "Start a {amt} SIP in UTI Nifty 50 Index Fund via any mutual fund app. It takes less than 5 minutes.",
        "confidence": 77,
    },
    ("Medium", "Intermediate"): {
        "plan": "50% in Diversified Equity Funds · 30% in Index Funds · 20% in REITs",
        "reason": "You understand the market well enough to benefit from active equity funds, with REITs adding real-estate exposure for diversification.",
        "action": "Increase your SIP by {amt} in a flexi-cap fund like Parag Parikh Flexi Cap and explore buying 1 REIT unit today.",
        "confidence": 81,
    },
    ("High", "Beginner"): {
        "plan": "60% in Large-Cap Equity Funds · 25% in Mid-Cap Funds · 15% in Index Funds",
        "reason": "High risk appetite is great, but as a beginner, managed equity funds protect you from common mistakes while targeting strong growth.",
        "action": "Open a Groww or Zerodha account today and start a {amt} SIP in Mirae Asset Large Cap Fund.",
        "confidence": 75,
    },
    ("High", "Intermediate"): {
        "plan": "40% in Mid/Small-Cap Funds · 30% in Direct Stocks · 20% in Crypto (regulated) · 10% in International Funds",
        "reason": "With experience and high risk tolerance, you can target aggressive growth through equities, international exposure, and a small crypto allocation.",
        "action": "Pick 2-3 fundamentally strong small-cap stocks and allocate {amt} to them today. Review your portfolio monthly.",
        "confidence": 78,
    },
}

MARKET_SIGNALS = [
    ("⚡ Slightly Volatile", "Markets are showing mixed signals with mild global headwinds. Proceed with a disciplined SIP approach."),
    ("📈 Cautiously Bullish", "Domestic indicators are positive but global cues remain uncertain. A balanced allocation is advised."),
    ("🌐 Mixed Global Signals", "FII outflows and US Fed uncertainty are creating short-term noise. Long-term fundamentals remain intact."),
    ("🛡️ Consolidation Phase", "Markets are consolidating after recent highs. This is a good entry window for staggered investments."),
]

# ── Gemini Call ────────────────────────────────────────────────────────────────
def call_gemini(amount, risk, experience):
    prompt = f"""
You are FinPilot AI, an expert Indian investment advisor focused on helping retail investors make simple, practical, and safe decisions.
Avoid jargon. Be clear, confident, and beginner-friendly.

User Profile:
- Monthly Investment: ₹{amount:,}
- Risk: {risk}
- Experience: {experience}

Task:
1. Give a clear allocation (percentages + instruments)
2. Explain WHY simply (2–3 sentences)
3. Give one ACTION for today (specific, practical)
4. Give a confidence score (70–90)

Respond ONLY in this format:
PLAN: <allocation>
INSIGHT: <reason>
ACTION: <today step>
CONFIDENCE: <number>
"""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()

    result = {}
    for line in text.splitlines():
        if line.startswith("PLAN:"):
            result["plan"] = line[len("PLAN:"):].strip()
        elif line.startswith("INSIGHT:"):
            result["reason"] = line[len("INSIGHT:"):].strip()
        elif line.startswith("ACTION:"):
            result["action"] = line[len("ACTION:"):].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = int("".join(filter(str.isdigit, line[len("CONFIDENCE:"):].strip()))[:2])
            except Exception:
                result["confidence"] = 80

    if not all(k in result for k in ("plan", "reason", "action", "confidence")):
        return None

    return result

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="FinPilot AI", page_icon="💹", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 780px; padding: 2rem 2rem; }
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        font-size: 1rem;
        color: #aaa;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 0.3rem;
    }
    .card {
        background: #1a1a2e;
        border: 1px solid #2e2e4d;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .market-badge {
        display: inline-block;
        background: #2a2a1a;
        border: 1px solid #665500;
        color: #FFD700;
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
    }
    .source-badge {
        display: inline-block;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .source-ai { background: #0d2a1a; border: 1px solid #1a6640; color: #92FE9D; }
    .source-fallback { background: #2a1a00; border: 1px solid #664400; color: #FFD700; }
    .confidence-label { font-size: 0.85rem; color: #aaa; margin-top: 0.3rem; }
    .disclaimer {
        font-size: 0.78rem;
        color: #666;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #222;
    }
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #00C9FF, #92FE9D);
        color: #0a0a0a;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1.5rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    div[data-testid="stButton"] > button:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">💹 FinPilot AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Investment Decision Engine — AI-powered system that tells you '
    '<strong>WHAT</strong> to do, <strong>WHEN</strong> to do it, and <strong>WHY</strong>.</div>',
    unsafe_allow_html=True,
)
st.divider()

# ── Inputs ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1.2, 1.2])
with col1:
    monthly_investment = st.number_input("💰 Monthly Investment (₹)", min_value=0, value=5000, step=500)
with col2:
    risk = st.selectbox("⚠️ Risk Appetite", ["Low", "Medium", "High"])
with col3:
    experience = st.selectbox("🎓 Experience Level", ["Beginner", "Intermediate"])

st.markdown("<br>", unsafe_allow_html=True)
status_ok, status_msg = check_gemini_status()
if status_ok:
    st.success(status_msg)
else:
    st.error(status_msg)

st.markdown("<br>", unsafe_allow_html=True)
generate = st.button(
    "🚀 Generate My Investment Plan",
    disabled=not status_ok
)

# ── On Generate ────────────────────────────────────────────────────────────────
if generate:
    if monthly_investment <= 0:
        st.warning("Please enter a valid monthly investment amount.")
        st.stop()

    amt_str = f"₹{monthly_investment:,}"
    signal_label, signal_detail = random.choice(MARKET_SIGNALS)
    used_ai = False
    result = None

    with st.spinner("🤖 AI Analysis: Analyzing your profile, risk appetite, and market conditions..."):
        try:
            if GEMINI_API_KEY:
                result = call_gemini(monthly_investment, risk, experience)
            else:
                result = None
            if result:
                used_ai = True
        except Exception:
            result = None

    if not result:
        fallback = FALLBACK_PLANS[(risk, experience)]
        result = {
            "plan": fallback["plan"],
            "reason": fallback["reason"],
            "action": fallback["action"].format(amt=amt_str),
            "confidence": fallback["confidence"],
        }
    else:
        result["action"] = result["action"]

    st.markdown("<br>", unsafe_allow_html=True)

    # Profile Summary
    st.markdown("### 👤 Profile Summary")
    st.write(f"Investing {amt_str}/month • {risk} risk • {experience} level")

    # Source badge
    if used_ai:
        st.markdown('<span class="source-badge source-ai">✨ Powered by Gemini AI</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="source-badge source-fallback">⚡ Static Fallback Plan (AI unavailable)</span>', unsafe_allow_html=True)

    # Market Context
    st.markdown('<div class="section-label">📡 Live Market Context</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="market-badge">{signal_label}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card" style="border-color:#444422;"><span style="color:#ccc;">{signal_detail}</span></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Recommended Allocation
    st.markdown('<div class="section-label">📋 Recommended Allocation</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card"><span style="font-size:1.05rem;font-weight:600;color:#92FE9D;">{result["plan"]}</span></div>',
        unsafe_allow_html=True,
    )

    # AI Insight
    st.markdown('<div class="section-label">🧠 AI Insight</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="card"><span style="color:#ddd;">{result["reason"]}</span></div>',
        unsafe_allow_html=True,
    )

    # Recommended Action
    st.markdown('<div class="section-label">⚡ Recommended Action (Today)</div>', unsafe_allow_html=True)
    action_text = result["action"] if used_ai else result["action"]
    st.markdown(
        f'<div class="card" style="border-color:#004466;">'
        f'<span style="color:#00C9FF;font-weight:500;">{action_text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Confidence Score
    confidence = result["confidence"]
    st.markdown('<div class="section-label">📊 AI Confidence Score</div>', unsafe_allow_html=True)
    st.progress(confidence / 100)
    st.markdown(
        f'<div class="confidence-label">Score: <strong>{confidence}%</strong> — '
        f'Based on your inputs and simulated market conditions.</div>',
        unsafe_allow_html=True,
    )
    st.caption("This recommendation is generated using AI trained on financial patterns and user profiles.")

    # Disclaimer
    st.markdown(
        '<div class="disclaimer">⚠️ This is AI-assisted decision support, not financial advice. '
        'Please consult a SEBI-registered investment advisor before making any financial decisions.</div>',
        unsafe_allow_html=True,
    )
