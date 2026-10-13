import streamlit as st

from document_loader import load_document
from text_splitter import split_documents
from vector_store import (
    load_embedding_model,
    build_vector_store,
    search_documents,
)
from rag_pipeline import answer_question


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
)


# ==========================================
# 2. CUSTOM CSS — PASTEL BLUE & PINK
# ==========================================
st.markdown(
    """
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(
            135deg,
            #f2f6ff 0%,
            #fff5f9 100%
        );
        color: #334155;
    }

    /* Hide Streamlit's running status widget */
    div[data-testid="stStatusWidget"] {
        display: none !important;
    }

    /* Hide progress bars */
    div[data-testid="stProgress"] {
        display: none !important;
    }

    /* Main title */
    .main-title {
        color: #5274b8;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-top: 12px;
        letter-spacing: -1px;
    }

    /* Subtitle */
    .subtitle {
        color: #7b86a4;
        text-align: center;
        font-size: 17px;
        margin-bottom: 25px;
    }

    /* Headings */
    h2, h3 {
        color: #5878bd !important;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e1e9fb;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 5px 18px rgba(120, 140, 190, 0.08);
    }

    /* Input fields */
    div[data-testid="stTextInput"] input {
        background: #ffffff;
        border: 1px solid #d9e3f8;
        border-radius: 12px;
        min-height: 44px;
    }

    /* Buttons */
    div.stButton > button,
    div.stFormSubmitButton > button {
        background: linear-gradient(
            100deg,
            #c4d8ff,
            #f4c9dc
        );
        color: #34476c;
        border: 1px solid #e3dff5;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.2s ease;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        border-color: #b9a8ed;
        color: #263858;
        transform: translateY(-1px);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f8f9ff;
        border-right: 1px solid #e7eafa;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid #e2e8f8;
        border-radius: 14px;
    }

    /* Answer card */
    .answer-card {
        background: #ffffff;
        border: 1px solid #e1e8f8;
        border-left: 5px solid #b7a8f5;
        border-radius: 18px;
        padding: 24px 28px;
        margin: 12px 0 24px 0;
        box-shadow: 0 6px 22px rgba(126, 145, 190, 0.10);
        color: #334155;
        line-height: 1.8;
    }

    .answer-heading {
        color: #5274b8;
        font-size: 25px;
        font-weight: 750;
        margin-bottom: 15px;
    }

    .answer-content {
        color: #334155;
        font-size: 16px;
        line-height: 1.85;
        overflow-wrap: anywhere;
    }

    /* Sources card */
    .sources-card {
        background: #fff8fb;
        border: 1px solid #f0dce8;
        border-left: 5px solid #efb7d1;
        border-radius: 16px;
        padding: 18px 22px;
        margin: 12px 0 22px 0;
        color: #526078;
        line-height: 1.8;
    }

    .sources-heading {
        color: #bd7098;
        font-size: 22px;
        font-weight: 750;
        margin-bottom: 10px;
    }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* Footer */
    .footer {
        color: #929bb0;
        text-align: center;
        font-size: 13px;
        padding: 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 3. HEADER
# ==========================================
st.markdown(
    '<div class="main-title">📚 DocuMind AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Your intelligent assistant for document understanding
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ==========================================
# 4. EMBEDDING MODEL — CACHED
# ==========================================
@st.cache_resource(show_spinner=False)
def get_embedding_model():
    return load_embedding_model()


# ==========================================
# 5. SESSION STATE
# ==========================================
if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "processed_files" not in st.session_state:
    st.session_state.processed_files = []


# ==========================================
# 6. SIDEBAR — DOCUMENT UPLOAD
# ==========================================
with st.sidebar:
    st.header("📂 Your documents")

    uploaded_files = st.file_uploader(
        "Upload your files",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT and MD.",
    )

    process_button = st.button(
        "✨ Process documents",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "Upload your files, process them, and ask "
        "questions about their content."
    )


# ==========================================
# 7. PROCESS DOCUMENTS
# ==========================================
if process_button:
    if not uploaded_files:
        st.warning("Please upload at least one document.")

    else:
        all_documents = []
        progress = st.progress(0, text="Reading documents...")

        try:
            for i, uploaded_file in enumerate(uploaded_files):
                extracted_documents = load_document(uploaded_file)
                all_documents.extend(extracted_documents)

                progress.progress(
                    (i + 1) / (len(uploaded_files) + 1),
                    text=f"Reading {uploaded_file.name}...",
                )

            chunks = split_documents(all_documents)

            if not chunks:
                raise ValueError(
                    "No readable text was found in the uploaded files."
                )

            progress.progress(
                0.75,
                text="Loading the embedding model...",
            )

            embedding_model = get_embedding_model()

            progress.progress(
                0.90,
                text="Building the search index...",
            )

            index = build_vector_store(chunks, embedding_model)

            st.session_state.index = index
            st.session_state.chunks = chunks
            st.session_state.processed_files = [
                file.name for file in uploaded_files
            ]

            st.success(
                f"Successfully processed {len(uploaded_files)} file(s) "
                f"and created {len(chunks)} text chunks."
            )

        except Exception as error:
            st.error(f"Processing failed: {error}")

        finally:
            progress.empty()


# ==========================================
# 8. DASHBOARD METRICS
# ==========================================
left, right = st.columns(2)

with left:
    st.metric(
        "📄 Documents processed",
        len(st.session_state.processed_files),
    )

with right:
    st.metric(
        "🧩 Text chunks indexed",
        len(st.session_state.chunks),
    )

st.divider()


# ==========================================
# 9. QUESTION AND ANSWER SECTION
# ==========================================
st.subheader("💬 Ask your documents")

st.caption(
    "Ask a question and get an answer grounded in your files."
)

if st.session_state.index is None:
    st.info(
        "Upload your documents from the sidebar and click "
        "**Process documents** to get started."
    )

else:
    with st.expander("📂 View processed files", expanded=False):
        for filename in st.session_state.processed_files:
            st.write(f"📄 {filename}")

    with st.form("question_form"):
        question = st.text_input(
            "Your question",
            placeholder=(
                "Example: What are the main points in this document?"
            ),
        )

        ask_button = st.form_submit_button(
            "🔎 Ask DocuMind AI",
            type="primary",
        )

    if ask_button:
        if not question.strip():
            st.warning("Please enter a question.")

        else:
            try:
                with st.spinner(
                    "Searching your documents and generating an answer..."
                ):
                    embedding_model = get_embedding_model()

                    retrieved_chunks = search_documents(
                        question=question,
                        index=st.session_state.index,
                        chunks=st.session_state.chunks,
                        model=embedding_model,
                        top_k=6,
                    )

                    result = answer_question(
                        question,
                        retrieved_chunks,
                    )

                # Display the answer inside a real Streamlit container
                st.markdown(
                    """
                    <div class="answer-card">
                        <div class="answer-heading">
                            📝 Answer
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Streamlit container provides a proper bordered card
                with st.container(border=True):
                    st.markdown(
                        '<div style="color:#5274b8;'
                        'font-size:22px;font-weight:750;'
                        'margin-bottom:12px;">📝 Answer</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(result["answer"])

                # Sources section
                st.markdown(
                    """
                    <div class="sources-card">
                        <div class="sources-heading">
                            📚 Sources
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    if result.get("sources"):
                        for source in result["sources"]:
                            st.markdown(f"📄 {source}")
                    else:
                        st.write("No sources available.")

            except Exception as error:
                st.error(
                    f"Could not generate an answer: {error}"
                )


# ==========================================
# 10. FOOTER
# ==========================================
st.divider()

st.markdown(
    """
    <div class="footer">
        DocuMind AI · RAG-powered document assistant
        <br>
        Local embeddings + FAISS + Groq
    </div>
    """,
    unsafe_allow_html=True,
)
