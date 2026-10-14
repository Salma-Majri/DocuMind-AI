import streamlit as st

from document_loader import load_document
from text_splitter import split_documents
from vector_store import (
    load_embedding_model,
    build_vector_store,
    search_documents,
)
from rag_pipeline import answer_question, generate_qcm


# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
)


# ==========================================
# CUSTOM STYLE
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f2f6ff, #fff5f9);
        color: #334155;
    }

    .main-title {
        color: #5274b8;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-top: 12px;
    }

    .subtitle {
        color: #7b86a4;
        text-align: center;
        font-size: 17px;
        margin-bottom: 25px;
    }

    h2, h3 {
        color: #5878bd !important;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e1e9fb;
        border-radius: 16px;
        padding: 18px;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background: linear-gradient(100deg, #c4d8ff, #f4c9dc);
        color: #34476c;
        border: 1px solid #e3dff5;
        border-radius: 12px;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background: #f8f9ff;
    }

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
# HEADER
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
# LOAD EMBEDDING MODEL
# ==========================================
@st.cache_resource(show_spinner=False)
def get_embedding_model():
    return load_embedding_model()


# ==========================================
# SESSION STATE
# ==========================================
if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = []

if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

if "generated_qcm" not in st.session_state:
    st.session_state.generated_qcm = []

if "qcm_answers" not in st.session_state:
    st.session_state.qcm_answers = {}

if "qcm_score" not in st.session_state:
    st.session_state.qcm_score = None


# ==========================================
# SIDEBAR: UPLOAD DOCUMENTS
# ==========================================
with st.sidebar:
    st.header("📂 Your documents")

    uploaded_files = st.file_uploader(
        "Upload your files",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
    )

    process_button = st.button(
        "✨ Process documents",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "Upload your files, process them, and ask questions "
        "about their content."
    )


# ==========================================
# PROCESS DOCUMENTS
# ==========================================
if process_button:
    if not uploaded_files:
        st.warning("Please upload at least one document.")
    else:
        progress = st.progress(0, text="Reading documents...")

        try:
            all_documents = []

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

            # Reset previous QCM when new documents are processed
            st.session_state.generated_qcm = []
            st.session_state.qcm_answers = {}
            st.session_state.qcm_score = None

            progress.progress(1.0, text="Completed!")

            st.success(
                f"Successfully processed {len(uploaded_files)} file(s) "
                f"and created {len(chunks)} text chunks."
            )

        except Exception as error:
            st.error(f"Processing failed: {error}")

        finally:
            progress.empty()


# ==========================================
# DASHBOARD METRICS
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "📄 Documents processed",
        len(st.session_state.processed_files),
    )

with col2:
    st.metric(
        "🧩 Text chunks indexed",
        len(st.session_state.chunks),
    )

st.divider()


# ==========================================
# DOCUMENT ASSISTANT
# ==========================================
st.subheader("📚 Learn from your documents")

st.caption(
    "Ask questions about your files or generate a multiple-choice "
    "quiz based on their content."
)

if st.session_state.index is None:
    st.info(
        "Upload your documents from the sidebar and click "
        "**Process documents** to get started."
    )

else:
    with st.expander("📂 View processed files"):
        for filename in st.session_state.processed_files:
            st.write(f"📄 {filename}")

    ask_tab, qcm_tab = st.tabs(
        ["💬 Ask your documents", "📝 Generate a QCM"]
    )

    # ======================================
    # TAB 1: ASK QUESTIONS
    # ======================================
    with ask_tab:
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

                    st.markdown("### 📝 Answer")
                    st.markdown(result["answer"])

                    st.markdown("### 📚 Sources")

                    sources = result.get("sources", [])

                    if sources:
                        for source in sources:
                            st.write(f"📄 {source}")
                    else:
                        st.write("No sources available.")

                except Exception as error:
                    st.error(
                        f"Could not generate an answer: {error}"
                    )

    # ======================================
    # TAB 2: GENERATE A QCM
    # ======================================
    with qcm_tab:
        st.markdown("#### Create a quiz from your documents")

        qcm_col1, qcm_col2 = st.columns(2)

        with qcm_col1:
            qcm_count = st.selectbox(
                "Number of questions",
                options=[5, 10, 15],
                index=0,
                key="qcm_count",
            )

        with qcm_col2:
            qcm_difficulty = st.selectbox(
                "Difficulty",
                options=["Easy", "Medium", "Hard"],
                index=1,
                key="qcm_difficulty",
            )

        if st.button(
            "✨ Generate my QCM",
            type="primary",
            key="generate_qcm_button",
        ):
            try:
                with st.spinner(
                    "Creating questions from your documents..."
                ):
                    qcm = generate_qcm(
                        chunks=st.session_state.chunks,
                        number_of_questions=qcm_count,
                        difficulty=qcm_difficulty,
                    )

                st.session_state.generated_qcm = qcm
                st.session_state.qcm_answers = {}
                st.session_state.qcm_score = None

                st.success("Your QCM is ready!")

            except Exception as error:
                st.error(f"Could not generate the QCM: {error}")

        qcm = st.session_state.generated_qcm

        if qcm:
            st.markdown("#### 🧠 Test your knowledge")

            with st.form("qcm_answer_form"):
                selected_answers = {}

                for i, item in enumerate(qcm):
                    st.markdown(
                        f"**Question {i + 1}. {item['question']}**"
                    )

                    options = item["options"]

                    option_labels = [
                        f"{letter}. {options[letter]}"
                        for letter in ["A", "B", "C", "D"]
                    ]

                    selected = st.radio(
                        "Choose one answer:",
                        options=option_labels,
                        index=None,
                        key=f"qcm_answer_{i}",
                        label_visibility="collapsed",
                    )

                    selected_answers[str(i)] = (
                        selected[0] if selected else None
                    )

                    st.divider()

                correct_button = st.form_submit_button(
                    "✅ Correct my QCM",
                    type="primary",
                )

            if correct_button:
                unanswered = [
                    i
                    for i, answer in selected_answers.items()
                    if answer is None
                ]

                if unanswered:
                    st.warning(
                        f"Please answer all {len(qcm)} questions "
                        "before correcting."
                    )

                else:
                    score = sum(
                        selected_answers[str(i)]
                        == item["correct_answer"]
                        for i, item in enumerate(qcm)
                    )

                    st.session_state.qcm_answers = selected_answers
                    st.session_state.qcm_score = score

            # ==================================
            # DISPLAY RESULTS
            # ==================================
            score = st.session_state.qcm_score

            if score is not None:
                total = len(qcm)
                percentage = round((score / total) * 100)

                st.markdown("### 🎉 Your result")

                st.metric(
                    "Score",
                    f"{score}/{total}",
                    f"{percentage}%",
                )

                st.progress(percentage / 100)

                for i, item in enumerate(qcm):
                    user_answer = st.session_state.qcm_answers.get(
                        str(i)
                    )

                    correct_answer = item["correct_answer"]
                    correct_text = item["options"][correct_answer]

                    if user_answer == correct_answer:
                        st.success(
                            f"Question {i + 1}: Correct! "
                            f"{correct_answer}. {correct_text}"
                        )
                    else:
                        st.error(
                            f"Question {i + 1}: Incorrect. "
                            f"Correct answer: {correct_answer}. "
                            f"{correct_text}"
                        )

                    if item.get("explanation"):
                        st.caption(
                            f"Explanation: {item['explanation']}"
                        )

                    if item.get("source"):
                        st.caption(
                            f"Source: {item['source']}"
                        )


# ==========================================
# FOOTER
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
