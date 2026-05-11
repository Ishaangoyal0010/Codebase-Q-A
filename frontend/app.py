import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Codebase Q&A", page_icon="🔍", layout="wide")

st.title("🔍 Codebase Q&A")
st.caption("Index any GitHub repo and ask questions about the code")
st.divider()

# sidebar
with st.sidebar:
    st.header("📦 Index a Repo")
    repo_url = st.text_input("GitHub URL", placeholder="https://github.com/user/repo")

    if st.button("🚀 Index Repo", use_container_width=True, type="primary"):
        if not repo_url.strip():
            st.error("paste a github url first")
        else:
            with st.spinner("cloning and indexing... this takes a minute ⏳"):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/index",
                        json={"repo_url": repo_url},
                        timeout=300
                    )
                    data = res.json()
                    if res.status_code == 200:
                        st.success(f"✅ indexed {data['files_indexed']} files, {data['chunks_stored']} chunks")
                        st.session_state.indexed = True
                        st.session_state.repo = repo_url
                        st.session_state.messages = []  # reset chat on new repo
                    else:
                        st.error(data.get("detail", "something went wrong"))
                except Exception as e:
                    st.error(f"could not reach backend: {e}")

    st.divider()

    if st.session_state.get("indexed"):
        st.success("✅ Repo indexed!")
        st.code(st.session_state.get("repo", ""), language="text")
        st.caption("ask anything about this codebase in the chat →")
    else:
        st.info("paste a github url above and click index to get started")

    st.divider()
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# chat area
if "messages" not in st.session_state:
    st.session_state.messages = []

# show welcome message(in start)
if not st.session_state.messages:
    st.info("👈 Index a repo first, then ask questions like:\n\n- *Where is auth handled?*\n- *What does the login function do?*\n- *How is the database connected?*")

# render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📁 view source references"):
                for src in msg["sources"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.code(src["reference"], language="text")
                    with col2:
                        st.metric("similarity", src["similarity"])

# chat input
question = st.chat_input("ask something about the code...")

if question:
    if not st.session_state.get("indexed"):
        st.warning("index a repo first using the sidebar!")
    else:
        # show user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # call backend and show answer
        with st.chat_message("assistant"):
            with st.spinner("searching codebase..."):
                try:
                    res = requests.post(
                        f"{BACKEND_URL}/ask",
                        json={"question": question, "top_k": 6},
                        timeout=60
                    )
                    data = res.json()

                    if res.status_code == 200:
                        answer = data["answer"]
                        sources = data["sources"]

                        st.markdown(answer)

                        with st.expander("📁 view source references"):
                            for src in sources:
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.code(src["reference"], language="text")
                                with col2:
                                    st.metric("similarity", src["similarity"])

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })

                    else:
                        err = data.get("detail", "something went wrong")
                        st.error(err)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"error: {err}",
                            "sources": []
                        })

                except Exception as e:
                    st.error(f"could not reach backend: {e}")
