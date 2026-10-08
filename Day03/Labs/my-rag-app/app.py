import io, json, sys
from datetime import date
from pathlib import Path

import numpy as np
import streamlit as st
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from askit_core import bedrock, config

# WHAT: set page shell and theme. WHY: this is the app identity and the saffron-on-white vibe.
st.set_page_config(page_title="AskMyPDF", page_icon="🦉", layout="wide")
st.markdown("""
<style>
    .stApp { background: #fffdf8; }
    .brand { font-size: 2.2rem; font-weight: 800; color: #7a4b00; margin: 0; }
    .tag { color: #c47c00; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    .stButton > button, .stDownloadButton > button { background: linear-gradient(180deg, #f7d784, #edb849); color: #2a1700; border: 1px solid #f1c76d; border-radius: 12px; }
    .stChatMessage { border-radius: 14px; }
    .card { background: #fff7e8; border: 1px solid #f0d8a4; border-radius: 12px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# WHAT: app state. WHY: index and chat persist between reruns without rebuilding every click.
if "chat" not in st.session_state: st.session_state.chat = []
if "index" not in st.session_state: st.session_state.index = {"pages": 0, "chunks": [], "vectors": np.empty((0, 512))}
if "pdf_name" not in st.session_state: st.session_state.pdf_name = ""

# WHAT: chunking helper. WHY: keep context in small windows with overlap for better retrieval.
def chunk_text(text, size=120, overlap=30):
    words = text.split()
    if not words: return []
    out, start = [], 0
    while start < len(words):
        end = min(start + size, len(words))
        out.append(" ".join(words[start:end]))
        if end == len(words): break
        start = max(start + 1, end - overlap)
    return out

# WHAT: embedding helper. WHY: every chunk and the question are turned into vectors for cosine similarity.
def embed_texts(texts):
    client = bedrock.client()
    embs = []
    for i in range(0, len(texts), 4):
        for text in texts[i:i+4]:
            try:
                body = json.dumps({"inputText": text, "dimensions": 512, "normalize": True})
                resp = client.invoke_model(modelId="amazon.titan-embed-text-v2:0", body=body, contentType="application/json", accept="application/json")
                embs.append(np.array(json.loads(resp["body"].read())["embedding"], dtype=float))
            except Exception:
                st.warning("AWS check failed. Check your .env keys, AWS region, and Titan model access. Then retry.")
                return []
    return embs

# WHAT: PDF loader. WHY: we only use uploaded text PDFs, and we track each page number.
def read_pdf(uploaded):
    reader = PdfReader(io.BytesIO(uploaded.read()))
    pages = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text: pages.append(text)
    return pages

# WHAT: index builder. WHY: this turns the PDF into chunks + vectors once, then reuses them in chat.
def build_index(uploaded):
    pages = read_pdf(uploaded)
    if not pages: st.warning("This PDF looks scanned or has no selectable text. Please upload a text PDF."); return
    chunks = []
    for pno, text in enumerate(pages, 1):
        for chunk in chunk_text(text, size=st.session_state.chunk_size, overlap=st.session_state.overlap):
            chunks.append({"page": pno, "text": chunk})
    prog = st.progress(0, text="Building index…")
    vectors = []
    for i in range(0, len(chunks), 4):
        batch = [c["text"] for c in chunks[i:i+4]]
        vecs = embed_texts(batch)
        if not vecs: return
        vectors.extend(vecs)
        prog.progress((i + len(batch)) / max(len(chunks), 1), text=f"Embedded {min(i + len(batch), len(chunks))}/{len(chunks)} chunks")
    prog.empty()
    st.session_state.index = {"pages": len(pages), "chunks": chunks, "vectors": np.array(vectors, dtype=float)}
    st.session_state.chat = []
    st.success(f"Indexed {len(pages)} pages and {len(chunks)} chunks.")

# WHAT: retrieval helper. WHY: cosine similarity picks the most relevant chunks for each question.
def retrieve(question, top_k):
    if not st.session_state.index["chunks"]: return []
    qv = embed_texts([question])
    if not qv: return []
    vects = st.session_state.index["vectors"]
    sims = (vects @ qv[0]) / (np.linalg.norm(vects, axis=1) * np.linalg.norm(qv[0]) + 1e-9)
    hits = []
    for idx in np.argsort(sims)[::-1][:top_k]:
        chunk = st.session_state.index["chunks"][int(idx)]
        hits.append({"page": chunk["page"], "text": chunk["text"], "score": float(sims[int(idx)])})
    return hits

# WHAT: answer generator. WHY: the model stays grounded to the PDF and cites pages like [p.3].
def ask_model(prompt):
    client = bedrock.client()
    try:
        msg = [{"role": "user", "content": [{"text": prompt}]}]
        resp = client.converse(modelId=config.SMALL_MODEL, messages=msg, inferenceConfig={"maxTokens": 500, "temperature": 0.2})
        return resp["output"]["message"]["content"][0]["text"]
    except Exception:
        st.warning("AWS check failed. Check your .env keys, AWS region, and Titan model access. Then retry.")
        return "I could not answer right now. Please retry after checking AWS settings."

# WHAT: UI shell. WHY: the user sees the app name, tagline, and sidebar controls quickly.
st.markdown('<div class="brand">🦉 AskMyPDF</div>', unsafe_allow_html=True)
st.markdown('<div class="tag">Upload. Ask. Done.</div>', unsafe_allow_html=True)

st.sidebar.header("Options")
st.session_state.chunk_size = st.sidebar.slider("Chunk size (words)", 60, 180, 120, 10)
st.session_state.overlap = st.sidebar.slider("Overlap (words)", 10, 60, 30, 5)
st.session_state.top_k = st.sidebar.slider("Top-K", 1, 6, 3)
if st.sidebar.button("Clear chat"): st.session_state.chat = []

today = date.today().strftime("%d %b %Y")
st.sidebar.markdown(f"""
<div class="card">
  <strong>About me</strong><br>
  Rajagopal, Team 2<br>
  <small>{today}</small><br>
  <em>Still debugging life, one PDF at a time.</em>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded is not None and uploaded.name != st.session_state.pdf_name:
    st.session_state.pdf_name = uploaded.name
    st.session_state.chat = []
    st.session_state.index = {"pages": 0, "chunks": [], "vectors": np.empty((0, 512))}

if uploaded is not None:
    if st.button("Build index"):
        build_index(uploaded)
    if st.session_state.index["chunks"]:
        st.caption(f"Pages: {st.session_state.index['pages']}  •  Chunks: {len(st.session_state.index['chunks'])}")

# WHAT: chat loop. WHY: each question is embedded, matched, and answered from the PDF only.
for role, msg in st.session_state.chat:
    with st.chat_message(role, avatar="🦉" if role == "assistant" else None):
        st.markdown(msg)

question = st.chat_input("Ask your PDF a question")
if st.button("Not in my PDF?"):
    st.session_state.chat.append(("user", "Who won the last cricket world cup?"))
    with st.chat_message("user"): st.markdown("Who won the last cricket world cup?")
    with st.chat_message("assistant", avatar="🦉"):
        st.markdown("I couldn’t find that in the PDF. This one is outside the document.")
        st.markdown('<div style="font-size:0.7rem;color:#7a4b00;">weak match</div>', unsafe_allow_html=True)
    st.session_state.chat.append(("assistant", "I couldn’t find that in the PDF. This one is outside the document."))

if question:
    hits = retrieve(question, st.session_state.top_k)
    context = "\n\n".join(f"[p.{h['page']}]\n{h['text']}" for h in hits)
    prompt = (
        "You are AskMyPDF, a calm senior engineer. Keep answers short, useful, and lightly funny. "
        "Answer ONLY from the context. If the answer is not in the context, say you could not find it in the PDF. "
        "Cite each fact with page numbers like [p.3].\n\nContext:\n" + context + "\n\nQuestion: " + question
    )
    with st.chat_message("user"): st.markdown(question)
    with st.chat_message("assistant", avatar="🦉"):
        answer = ask_model(prompt)
        st.markdown(answer)
        badge = "grounded" if hits and hits[0]["score"] >= 0.35 else "weak match"
        st.markdown(f'<div style="display:inline-block;background:#fff7e8;border:1px solid #f0d8a4;border-radius:999px;padding:4px 8px;color:#7a4b00;font-size:0.7rem;">{badge}</div>', unsafe_allow_html=True)
        with st.expander("Sources"):
            for h in hits:
                st.markdown(f"**Page {h['page']}** — score {h['score']:.2f}")
                st.write(h['text'])
    st.session_state.chat.append(("user", question))
    st.session_state.chat.append(("assistant", answer))

if st.session_state.chat:
    md = "\n\n".join(f"{role}:\n{msg}" for role, msg in st.session_state.chat)
    st.download_button("Download chat", data=md, file_name="askmypdf-chat.md", mime="text/markdown")

st.markdown('<div style="margin-top:1.5rem;border-top:1px solid #f0d8a4;padding-top:0.8rem;text-align:center;color:#4a3a1d;">Built by "Rajagopal, Team 2" with vibe coding at DevPro Academy</div>', unsafe_allow_html=True)
