import streamlit as st
from pathlib import Path
import json
from datetime import datetime

from pdf_processor import (
    extract_pdf_text,
    create_sample_study_material,
    get_pdf_metadata
)
from rag_pipeline import create_vector_store

from mcq_generator import (
    answer_question,
    generate_summary,
    generate_mcqs,
    generate_flashcards,
    generate_study_plan,
    analyze_quiz_performance,
    export_quiz_to_markdown
)


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="ExamPrep AI - Government Exam Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# 2. LOAD CSS
# =====================================================

def load_css():
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        css = css_file.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()


# =====================================================
# 3. SESSION STATE INITIALIZATION
# =====================================================

defaults = {
    # Original keys preserved
    "navigation": "🏠 Dashboard",
    "vectorstore": None,
    "document_name": None,
    "total_pages": 0,
    "total_chunks": 0,
    "total_words": 0,
    "questions": [],
    "source_pages": [],
    "quiz_result": None,
    "quiz_version": 0,
    "chat_history": [],
    "summary": None,
    "summary_pages": [],
    "processed_file_name": None,

    # Enhanced keys for new features
    "exam_target": "UPSC Civil Services",
    "language": "English",
    "selected_model": "gemini-3.5-flash",
    "negative_marking": 0.33,
    "flashcards": [],
    "study_plan": None,
    "ai_diagnosis": None,
    "study_notes": [],
    "quiz_history": [],
    "sample_loaded": False,
    "flashcard_flipped": {}
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 4. NAVIGATION & HELPER FUNCTIONS
# =====================================================

def navigate_to(page):
    st.session_state.navigation = page


def show_header(title, description):
    st.markdown(
        f"""
        <div style="margin-bottom:25px;">
            <h1 style="font-size:30px;margin-bottom:5px;">
                {title}
            </h1>
            <p style="color:#64748b;font-size:15px;">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


def document_required():
    if st.session_state.vectorstore is None:
        st.warning("Please upload or load study material first.")

        col1, col2 = st.columns(2)
        with col1:
            st.button(
                "📄 Upload Study Material",
                use_container_width=True,
                on_click=navigate_to,
                args=("📄 Upload Study Material",)
            )
        with col2:
            if st.button("📚 Load Pre-loaded Indian Polity Guide", use_container_width=True, type="primary"):
                load_sample_document()
                st.rerun()

        return False

    return True


def show_footer():
    st.markdown(
        """
        <div class="footer">
            <b>ExamPrep AI</b> | Smart Government Exam Preparation Assistant<br>
            Designed for UPSC CSE, SSC CGL/CHSL, Banking, State PSCs (APPSC / TSPSC) & Railways<br>
            Built with Python | Streamlit | RAG | FAISS | Google Gemini
        </div>
        """,
        unsafe_allow_html=True
    )


def load_sample_document():
    """Generates and indexes the sample Indian Polity & Governance PDF."""
    try:
        sample_path = create_sample_study_material(Path(__file__).parent / "documents")
        pages = extract_pdf_text(sample_path)
        vectorstore, total_chunks = create_vector_store(pages)
        total_words = sum(len(p["text"].split()) for p in pages)

        st.session_state.vectorstore = vectorstore
        st.session_state.document_name = "Indian_Polity_and_Governance_UPSC_SSC.pdf"
        st.session_state.total_pages = len(pages)
        st.session_state.total_chunks = total_chunks
        st.session_state.total_words = total_words
        st.session_state.processed_file_name = "Indian_Polity_and_Governance_UPSC_SSC.pdf"
        st.session_state.sample_loaded = True

        # Reset old results
        st.session_state.questions = []
        st.session_state.source_pages = []
        st.session_state.quiz_result = None
        st.session_state.chat_history = []
        st.session_state.summary = None
        st.session_state.flashcards = []
        st.session_state.study_plan = None
        st.session_state.ai_diagnosis = None
        st.session_state.quiz_version += 1

        st.success("Pre-loaded Indian Polity & Governance study guide loaded successfully!")
    except Exception as e:
        st.error(f"Failed to load sample material: {str(e)}")


# =====================================================
# 5. SIDEBAR
# =====================================================

pages = [
    "🏠 Dashboard",
    "📄 Upload Study Material",
    "💬 Ask AI",
    "📝 Practice MCQs & Quiz",
    "🗂️ Flashcards (Active Recall)",
    "📖 Topic Summary & Notes",
    "📊 Quiz Results & AI Analysis",
    "📅 Exam Study Planner",
    "📈 Performance Analytics",
    "📥 Export Center"
]

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:15px 5px 10px;">
            <div style="font-size:38px;">📚</div>
            <h2 style="color:white !important;margin:4px 0;font-size:22px;">
                ExamPrep AI
            </h2>
            <p style="font-size:12px;color:#c5d3e5;margin:0;">
                Smart Government Exam Preparation
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### MAIN MENU")
    selected_page = st.radio(
        "Navigation",
        pages,
        key="navigation",
        label_visibility="collapsed"
    )

    st.divider()

    # Exam Preferences
    st.markdown("### 🎯 EXAM SETTINGS")
    exam_options = [
        "UPSC Civil Services",
        "SSC CGL / CHSL",
        "Banking (IBPS / SBI)",
        "State PSC (APPSC / TSPSC)",
        "Railway (RRB NTPC)"
    ]
    st.session_state.exam_target = st.selectbox(
        "Target Exam",
        exam_options,
        index=exam_options.index(st.session_state.exam_target) if st.session_state.exam_target in exam_options else 0
    )

    lang_options = [
        "English",
        "తెలుగు (Telugu)",
        "हिन्दी (Hindi)"
    ]
    st.session_state.language = st.selectbox(
        "Language / భాష",
        lang_options,
        index=lang_options.index(st.session_state.language) if st.session_state.language in lang_options else 0
    )

    st.divider()

    st.markdown("### DOCUMENT STATUS")
    if st.session_state.vectorstore is not None:
        st.success("Document Active")
        st.caption(f"📄 {st.session_state.document_name}")
        st.caption(
            f"{st.session_state.total_pages} pages | "
            f"{st.session_state.total_chunks} chunks | "
            f"{st.session_state.total_words} words"
        )
    else:
        st.info("No study material loaded")
        if st.button("📚 Load Sample Guide", use_container_width=True):
            load_sample_document()
            st.rerun()

    st.divider()

    if st.button("🔄 Clear All & Reset", use_container_width=True):
        st.session_state.vectorstore = None
        st.session_state.document_name = None
        st.session_state.total_pages = 0
        st.session_state.total_chunks = 0
        st.session_state.total_words = 0
        st.session_state.questions = []
        st.session_state.source_pages = []
        st.session_state.quiz_result = None
        st.session_state.chat_history = []
        st.session_state.summary = None
        st.session_state.flashcards = []
        st.session_state.study_plan = None
        st.session_state.ai_diagnosis = None
        st.session_state.quiz_version += 1
        st.rerun()


# =====================================================
# 6. DASHBOARD
# =====================================================

if selected_page == "🏠 Dashboard":

    st.markdown(
        f"""
        <div class="hero-card">
            <h1>Welcome to ExamPrep AI 👋</h1>
            <p>
                Your intelligent learning companion for <b>{st.session_state.exam_target}</b> and
                all competitive examinations. Upload study materials, ask AI questions, practice
                exam-pattern MCQs with negative marking, memorize with flashcards, and track your progress.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    show_header(
        "Your Learning Dashboard",
        f"Customized for {st.session_state.exam_target} Preparation"
    )

    # 3 Stat Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="dashboard-card">
                <div class="card-icon">📄</div>
                <h3>Study Materials</h3>
                <p>Upload your syllabus PDFs or use our pre-loaded Indian Polity guide.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="dashboard-card">
                <div class="card-icon">🤖</div>
                <h3>AI Exam Mentor</h3>
                <p>Ask in-depth questions in English, Telugu, or Hindi using RAG.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="dashboard-card">
                <div class="card-icon">📝</div>
                <h3>Mock Tests & MCQs</h3>
                <p>Generate authentic exam questions with negative marking & analysis.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # Metrics Row
    col4, col5, col6, col7 = st.columns(4)

    with col4:
        st.metric("Document Pages", st.session_state.total_pages)

    with col5:
        st.metric("Knowledge Chunks", st.session_state.total_chunks)

    with col6:
        result = st.session_state.quiz_result
        score_text = f"{result['percentage']:.1f}%" if result else "Not attempted"
        st.metric("Latest Quiz Score", score_text)

    with col7:
        st.metric("Quizzes Completed", len(st.session_state.quiz_history))

    st.divider()

    st.subheader("🚀 Quick Actions")
    q1, q2, q3, q4 = st.columns(4)

    with q1:
        st.button(
            "📄 Upload PDF",
            use_container_width=True,
            on_click=navigate_to,
            args=("📄 Upload Study Material",)
        )

    with q2:
        st.button(
            "💬 Ask AI",
            use_container_width=True,
            on_click=navigate_to,
            args=("💬 Ask AI",)
        )

    with q3:
        st.button(
            "📝 Practice MCQs",
            use_container_width=True,
            on_click=navigate_to,
            args=("📝 Practice MCQs & Quiz",)
        )

    with q4:
        st.button(
            "🗂️ Flashcards",
            use_container_width=True,
            on_click=navigate_to,
            args=("🗂️ Flashcards (Active Recall)",)
        )

    st.write("")

    # Document Status Banner / Quick Loader
    if st.session_state.vectorstore is None:
        st.info("💡 You have not loaded any study material yet. You can upload a PDF or load our pre-loaded Indian Polity guide with one click.")
        if st.button("📚 Click Here to Load Pre-loaded Indian Polity Study Guide", type="primary", use_container_width=True):
            load_sample_document()
            st.rerun()
    else:
        st.success(f"✅ Active Study Material: **{st.session_state.document_name}** ({st.session_state.total_pages} pages, {st.session_state.total_chunks} chunks)")


# =====================================================
# 7. UPLOAD STUDY MATERIAL
# =====================================================

elif selected_page == "📄 Upload Study Material":

    show_header(
        "Upload Study Material",
        "Upload your government examination study PDF or load pre-loaded notes."
    )

    st.markdown(
        """
        <div class="content-card">
            <h3>📚 Add Your Study Document</h3>
            <p style="color:#64748b;">
                Upload materials for UPSC, SSC, Banking, State PSCs (APPSC / TSPSC), and Railways.
                The AI will extract text, build semantic embeddings, and prepare your personalized question bank.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_up1, col_up2 = st.columns([2, 1])

    with col_up2:
        st.markdown("#### ⚡ Fast-Track Option")
        st.markdown("Don't have a PDF ready? Use our comprehensive pre-loaded **Indian Polity & Governance** exam notes (5 pages).")
        if st.button("📚 Load Pre-loaded Polity Guide", use_container_width=True, type="secondary"):
            load_sample_document()
            st.rerun()

    with col_up1:
        uploaded_file = st.file_uploader(
            "Choose your PDF document",
            type=["pdf"],
            help="Select a study PDF from your computer.",
            key="study_pdf_uploader"
        )

        if uploaded_file is not None:
            st.success("PDF uploaded successfully!")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("File Name", uploaded_file.name)
            with col2:
                st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")

            st.write("")

            if st.button(
                "⚡ Process PDF and Build RAG Knowledge Base",
                use_container_width=True,
                type="primary"
            ):
                try:
                    with st.spinner("Extracting PDF text and generating semantic embeddings..."):
                        pages = extract_pdf_text(uploaded_file)
                        vectorstore, total_chunks = create_vector_store(
                            pages,
                            save_dir=Path(__file__).parent / "vectorstore"
                        )
                        total_words = sum(len(page["text"].split()) for page in pages)

                        st.session_state.vectorstore = vectorstore
                        st.session_state.document_name = uploaded_file.name
                        st.session_state.total_pages = len(pages)
                        st.session_state.total_chunks = total_chunks
                        st.session_state.total_words = total_words
                        st.session_state.processed_file_name = uploaded_file.name
                        st.session_state.sample_loaded = False

                        # Reset old document results
                        st.session_state.questions = []
                        st.session_state.source_pages = []
                        st.session_state.quiz_result = None
                        st.session_state.chat_history = []
                        st.session_state.summary = None
                        st.session_state.flashcards = []
                        st.session_state.study_plan = None
                        st.session_state.ai_diagnosis = None
                        st.session_state.quiz_version += 1

                    st.success(f"PDF processed successfully! {len(pages)} pages converted into {total_chunks} chunks.")
                    st.balloons()
                except Exception as e:
                    st.error(f"PDF processing failed: {str(e)}")

    # Show active document stats
    if st.session_state.vectorstore is not None:
        st.divider()
        st.subheader("📊 Active Document Information")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Pages", st.session_state.total_pages)
        c2.metric("Total Words", st.session_state.total_words)
        c3.metric("Indexed Chunks", st.session_state.total_chunks)

        st.success(f"Active document: **{st.session_state.document_name}**")
        st.info("Your knowledge base is ready! You can now ask questions, generate MCQs, or build flashcards.")

        st.subheader("🚀 Continue Learning")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("💬 Start Asking AI", use_container_width=True, on_click=navigate_to, args=("💬 Ask AI",))
        with c2:
            st.button("📝 Practice MCQs", use_container_width=True, on_click=navigate_to, args=("📝 Practice MCQs & Quiz",))
        with c3:
            st.button("📖 Topic Summary", use_container_width=True, on_click=navigate_to, args=("📖 Topic Summary & Notes",))


# =====================================================
# 8. ASK AI
# =====================================================

elif selected_page == "💬 Ask AI":

    show_header(
        "Ask Your AI Exam Mentor",
        f"Get accurate, syllabus-aligned answers for {st.session_state.exam_target}."
    )

    if document_required():
        st.info(f"Answering from: **{st.session_state.document_name}** | Language: **{st.session_state.language}**")

        col1, col2 = st.columns([3, 1])
        with col2:
            exam_mode = st.selectbox(
                "Answer Style",
                ["UPSC In-Depth", "SSC Quick Fact", "Mains Conceptual", "Standard"],
                index=0
            )

        with st.form("ask_ai_form"):
            question = st.text_input(
                "Enter your question",
                placeholder="Example: What are the constitutional grounds for impeaching the President under Article 61?"
            )
            ask_submitted = st.form_submit_button("🤖 Get AI Answer", use_container_width=True)

        if ask_submitted:
            if question.strip():
                try:
                    with st.spinner("Searching document chunks and formulating answer..."):
                        answer, pages = answer_question(
                            st.session_state.vectorstore,
                            question.strip(),
                            language=st.session_state.language,
                            exam_focus=f"{st.session_state.exam_target} ({exam_mode})"
                        )

                    st.session_state.chat_history.append({
                        "question": question.strip(),
                        "answer": answer,
                        "pages": pages,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    st.success("Answer generated successfully!")
                except Exception as e:
                    st.error(f"AI answer generation failed: {str(e)}")
            else:
                st.warning("Please enter a question.")

        st.divider()

        # Questions & Answers History
        col_hdr, col_btn = st.columns([3, 1])
        with col_hdr:
            st.subheader("💡 Questions & Answers")
        with col_btn:
            if st.session_state.chat_history:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

        if st.session_state.chat_history:
            for idx, item in enumerate(reversed(st.session_state.chat_history)):
                with st.container(border=True):
                    st.markdown(f"**You:** {item['question']}")
                    st.markdown("**AI Answer:**")
                    st.markdown(item["answer"])
                    st.caption(f"Source pages: {item['pages']} | Time: {item.get('timestamp', '')}")

                    # Save to Notes button
                    if st.button(f"💾 Save to Study Notes", key=f"save_note_{idx}"):
                        st.session_state.study_notes.append({
                            "title": item["question"],
                            "content": item["answer"],
                            "source": f"{st.session_state.document_name} (Pages: {item['pages']})"
                        })
                        st.toast("Saved to your Study Notes!")
        else:
            st.info("Ask your first question to begin.")


# =====================================================
# 9. PRACTICE MCQs & QUIZ (TIMED & NEGATIVE MARKING)
# =====================================================

elif selected_page == "📝 Practice MCQs & Quiz":

    show_header(
        "AI Mock Test & MCQ Practice",
        f"Generate authentic {st.session_state.exam_target} practice questions with negative marking."
    )

    if document_required():
        st.success(f"Active material: **{st.session_state.document_name}**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            number_of_questions = st.selectbox("Number of Questions", [5, 10, 15, 20], index=1)

        with col2:
            difficulty = st.selectbox("Difficulty Level", ["Medium", "Easy", "Hard"], index=0)

        with col3:
            neg_options = {
                "UPSC Standard (-0.33)": 0.33,
                "SSC / Banking (-0.25)": 0.25,
                "Half Mark (-0.50)": 0.50,
                "No Negative Marking (0.0)": 0.0
            }
            selected_neg = st.selectbox("Negative Marking", list(neg_options.keys()), index=0)
            st.session_state.negative_marking = neg_options[selected_neg]

        with col4:
            topic_filter = st.text_input(
                "Topic Focus (Optional)",
                placeholder="e.g. Fundamental Rights, Executive"
            )

        if st.button("✨ Generate Exam MCQs", use_container_width=True, type="primary"):
            try:
                with st.spinner(f"Generating {number_of_questions} {difficulty} questions for {st.session_state.exam_target}..."):
                    questions, pages = generate_mcqs(
                        st.session_state.vectorstore,
                        number_of_questions,
                        difficulty,
                        exam_type=st.session_state.exam_target,
                        topic=topic_filter,
                        language=st.session_state.language
                    )

                    st.session_state.questions = questions
                    st.session_state.source_pages = pages
                    st.session_state.quiz_result = None
                    st.session_state.ai_diagnosis = None
                    st.session_state.quiz_version += 1

                if questions:
                    st.success(f"Generated {len(questions)} authentic exam MCQs!")
                else:
                    st.warning("No questions generated. Try adjusting the topic filter or question count.")
            except Exception as e:
                st.error(f"MCQ generation failed: {str(e)}")

        questions = st.session_state.questions

        if questions:
            st.divider()
            st.subheader(f"📝 {st.session_state.exam_target} Practice Test")
            st.caption(f"Source pages: {st.session_state.source_pages} | Negative marking per incorrect answer: -{st.session_state.negative_marking:.2f}")

            quiz_version = st.session_state.quiz_version

            with st.form(key=f"quiz_form_{quiz_version}"):
                user_answers = []

                for index, q in enumerate(questions, start=1):
                    st.markdown(f"**Question {index}:** {q['question']}")

                    answer = st.radio(
                        "Select your answer:",
                        ["A", "B", "C", "D"],
                        format_func=lambda x, opts=q["options"]: f"{x}. {opts[x]}",
                        key=f"quiz_answer_{quiz_version}_{index}",
                        index=None
                    )
                    user_answers.append(answer)
                    st.divider()

                submitted = st.form_submit_button("📊 Submit Mock Test", use_container_width=True)

            if submitted:
                total = len(questions)
                attempted = sum(1 for a in user_answers if a is not None)
                correct = sum(
                    user_ans == q["answer"]
                    for user_ans, q in zip(user_answers, questions)
                    if user_ans is not None
                )
                incorrect = attempted - correct
                unattempted = total - attempted

                penalty = incorrect * st.session_state.negative_marking
                net_score = max(0.0, float(correct) - penalty)
                percentage = (correct / total) * 100 if total > 0 else 0.0

                result_data = {
                    "correct": correct,
                    "incorrect": incorrect,
                    "unattempted": unattempted,
                    "penalty": penalty,
                    "net_score": net_score,
                    "total": total,
                    "percentage": percentage,
                    "answers": user_answers,
                    "questions": questions.copy(),
                    "exam_type": st.session_state.exam_target,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p")
                }

                st.session_state.quiz_result = result_data
                st.session_state.quiz_history.append(result_data)

                st.success("Test submitted! Your score has been calculated with negative marking.")
                st.button(
                    "📊 View Detailed Results & AI Analysis",
                    use_container_width=True,
                    on_click=navigate_to,
                    args=("📊 Quiz Results & AI Analysis",)
                )

        else:
            st.info("Choose your preferred question count and difficulty, then click **Generate Exam MCQs**.")


# =====================================================
# 10. FLASHCARDS & ACTIVE RECALL
# =====================================================

elif selected_page == "🗂️ Flashcards (Active Recall)":

    show_header(
        "Active Recall Flashcards",
        "Master high-yield articles, dates, amendments, and definitions."
    )

    if document_required():
        st.success(f"Study Material: **{st.session_state.document_name}**")

        col1, col2 = st.columns([2, 1])
        with col1:
            card_topic = st.text_input("Flashcard Topic Focus (Optional)", placeholder="e.g. Fundamental Rights, Articles")
        with col2:
            card_count = st.selectbox("Number of Flashcards", [5, 10, 15], index=1)

        if st.button("✨ Generate Flashcards", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generating flashcards for active recall..."):
                    cards = generate_flashcards(
                        st.session_state.vectorstore,
                        count=card_count,
                        topic=card_topic,
                        language=st.session_state.language
                    )
                    st.session_state.flashcards = cards
                    st.session_state.flashcard_flipped = {}

                if cards:
                    st.success(f"Generated {len(cards)} active recall flashcards!")
                else:
                    st.warning("No flashcards generated. Try another topic.")
            except Exception as e:
                st.error(f"Flashcard generation failed: {str(e)}")

        flashcards = st.session_state.flashcards

        if flashcards:
            st.divider()
            st.subheader("🗂️ Flashcard Deck")
            st.caption("Click 'Reveal Answer' to test your recall.")

            for idx, card in enumerate(flashcards, 1):
                flipped = st.session_state.flashcard_flipped.get(idx, False)

                with st.container(border=True):
                    col_cat, col_flip = st.columns([3, 1])
                    with col_cat:
                        st.markdown(f"**Card #{idx}** &nbsp; | &nbsp; Category: `{card.get('category', 'General')}`")

                    st.markdown(f"### {card.get('front', '')}")

                    if flipped:
                        st.markdown(f"**Answer / Key Fact:**")
                        st.info(card.get("back", ""))

                    with col_flip:
                        btn_label = "Hide Answer" if flipped else "👁️ Reveal Answer"
                        if st.button(btn_label, key=f"flip_btn_{idx}", use_container_width=True):
                            st.session_state.flashcard_flipped[idx] = not flipped
                            st.rerun()
        else:
            st.info("Click **Generate Flashcards** to build a deck from your study material.")


# =====================================================
# 11. TOPIC SUMMARY & CHEAT SHEETS
# =====================================================

elif selected_page == "📖 Topic Summary & Notes":

    show_header(
        "Topic Summary & Cheat Sheets",
        "Generate high-yield summaries, article cheat sheets, or mind map outlines."
    )

    if document_required():
        with st.form("summary_form"):
            topic = st.text_input(
                "Enter topic to summarize",
                placeholder="Example: Fundamental Rights and Writs under Article 32"
            )

            col1, col2 = st.columns(2)
            with col1:
                summary_style = st.selectbox(
                    "Summary Format",
                    [
                        "Comprehensive",
                        "High-Yield Facts & Dates",
                        "Exam Bullet Points",
                        "Key Constitutional Articles / Formulas",
                        "Mind Map / Outline"
                    ],
                    index=0
                )
            with col2:
                summary_lang = st.selectbox(
                    "Language",
                    ["English", "తెలుగు (Telugu)", "हिन्दी (Hindi)"],
                    index=["English", "తెలుగు (Telugu)", "हिन्दी (Hindi)"].index(st.session_state.language)
                )

            summary_submitted = st.form_submit_button("📖 Generate Study Summary", use_container_width=True)

        if summary_submitted:
            if topic.strip():
                try:
                    with st.spinner("Synthesizing summary from retrieved chunks..."):
                        summary, pages = generate_summary(
                            st.session_state.vectorstore,
                            topic.strip(),
                            summary_style=summary_style,
                            language=summary_lang
                        )
                    st.session_state.summary = summary
                    st.session_state.summary_pages = pages
                    st.success("Summary generated successfully!")
                except Exception as e:
                    st.error(f"Summary generation failed: {str(e)}")
            else:
                st.warning("Please enter a topic.")

        if st.session_state.summary:
            st.divider()
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                st.subheader("📖 Generated Summary")
            with col_s2:
                st.download_button(
                    "📥 Download Summary (.md)",
                    data=st.session_state.summary,
                    file_name=f"Summary_{topic.strip()[:20]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with st.container(border=True):
                st.markdown(st.session_state.summary)
                st.caption(f"Source pages: {st.session_state.summary_pages}")

                if st.button("💾 Save to Study Notes", key="save_summary_btn"):
                    st.session_state.study_notes.append({
                        "title": f"Summary: {topic.strip()}",
                        "content": st.session_state.summary,
                        "source": f"{st.session_state.document_name} (Pages: {st.session_state.summary_pages})"
                    })
                    st.toast("Saved to Study Notes!")
        else:
            st.info("Enter a topic above to generate study notes.")


# =====================================================
# 12. QUIZ RESULTS & AI ANALYSIS
# =====================================================

elif selected_page == "📊 Quiz Results & AI Analysis":

    show_header(
        "Quiz Performance & AI Diagnostics",
        "Review your score, negative marking breakdown, and targeted AI revision tips."
    )

    result = st.session_state.quiz_result

    if result is None:
        st.info("You have not submitted a quiz yet. Generate questions and take a test first.")
        st.button(
            "Go to MCQ Generator",
            use_container_width=True,
            on_click=navigate_to,
            args=("📝 Practice MCQs & Quiz",)
        )
    else:
        correct = result["correct"]
        incorrect = result.get("incorrect", 0)
        unattempted = result.get("unattempted", 0)
        penalty = result.get("penalty", 0.0)
        net_score = result.get("net_score", float(correct))
        total = result["total"]
        percentage = result["percentage"]

        # 4 Score Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Correct (+1 each)", f"{correct}/{total}")
        col2.metric("Incorrect", f"{incorrect}")
        col3.metric("Negative Penalty", f"-{penalty:.2f}")
        col4.metric("Net Score", f"{net_score:.2f}/{total}")

        st.subheader("Performance Overview")
        st.progress(percentage / 100)

        if percentage >= 70:
            st.success("🌟 Excellent performance! You are on track for qualification.")
        elif percentage >= 40:
            st.info("👍 Good effort! Focus on minimizing negative marks in tricky questions.")
        else:
            st.warning("⚠️ Needs Revision. Thoroughly review incorrect answers and explanations below.")

        st.divider()

        # AI Weakness Analysis Section
        st.subheader("🤖 AI Diagnostic & Weak Area Analysis")
        st.write("Get a personalized AI critique identifying your conceptual weak spots and revision action plan.")

        if st.button("🔍 Run AI Performance Diagnostics", type="primary"):
            try:
                with st.spinner("Gemini is analyzing your mistakes and concept gaps..."):
                    diagnosis = analyze_quiz_performance(
                        result,
                        exam_type=st.session_state.exam_target,
                        language=st.session_state.language
                    )
                    st.session_state.ai_diagnosis = diagnosis
                st.success("Diagnostic analysis completed!")
            except Exception as e:
                st.error(f"Diagnostics failed: {str(e)}")

        if st.session_state.ai_diagnosis:
            with st.container(border=True):
                st.markdown(st.session_state.ai_diagnosis)

        st.divider()

        # Detailed Question Review
        st.subheader("📋 Question-by-Question Solution Review")

        for index, q in enumerate(result["questions"]):
            user_answer = result["answers"][index] if index < len(result["answers"]) else None
            correct_answer = q["answer"]
            is_correct = (user_answer == correct_answer)

            header_text = f"Q{index + 1}: {q['question'][:90]}... - " + ("✅ Correct" if is_correct else ("⚠️ Unattempted" if user_answer is None else "❌ Incorrect"))

            with st.expander(header_text):
                st.markdown(f"**Full Question:** {q['question']}")

                for opt_key in ["A", "B", "C", "D"]:
                    opt_text = q["options"].get(opt_key, "")
                    if opt_key == correct_answer:
                        st.markdown(f"- **({opt_key}) {opt_text}** ✅ *(Correct Answer)*")
                    elif opt_key == user_answer:
                        st.markdown(f"- **({opt_key}) {opt_text}** ❌ *(Your Choice)*")
                    else:
                        st.markdown(f"- ({opt_key}) {opt_text}")

                st.write("")
                st.info(f"**Detailed Explanation:** {q.get('explanation', '')}")

        st.divider()

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            st.button(
                "📝 Practice Another Quiz",
                use_container_width=True,
                on_click=navigate_to,
                args=("📝 Practice MCQs & Quiz",)
            )
        with c_act2:
            export_md = export_quiz_to_markdown(
                result,
                document_name=st.session_state.document_name,
                exam_type=st.session_state.exam_target
            )
            st.download_button(
                "📥 Download Test Paper & Solutions (.md)",
                data=export_md,
                file_name=f"MockTest_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True
            )


# =====================================================
# 13. EXAM STUDY PLANNER
# =====================================================

elif selected_page == "📅 Exam Study Planner":

    show_header(
        "AI Exam Study Planner",
        f"Generate a customized revision roadmap for {st.session_state.exam_target}."
    )

    if document_required():
        st.success(f"Creating schedule based on: **{st.session_state.document_name}**")

        col1, col2 = st.columns(2)
        with col1:
            days = st.selectbox("Days Available Until Exam", [7, 15, 30, 45, 60], index=0)
        with col2:
            daily_hours = st.selectbox("Daily Study Hours", [2, 3, 4, 6, 8], index=1)

        if st.button("📅 Generate Personalized Study Schedule", use_container_width=True, type="primary"):
            try:
                with st.spinner("Analyzing syllabus contents and constructing revision milestones..."):
                    plan = generate_study_plan(
                        st.session_state.vectorstore,
                        exam_type=st.session_state.exam_target,
                        days=days,
                        daily_hours=daily_hours,
                        language=st.session_state.language
                    )
                    st.session_state.study_plan = plan
                st.success("Study schedule generated!")
            except Exception as e:
                st.error(f"Study plan generation failed: {str(e)}")

        if st.session_state.study_plan:
            st.divider()
            col_p1, col_p2 = st.columns([3, 1])
            with col_p1:
                st.subheader(f"📅 Your {days}-Day Preparation Roadmap")
            with col_p2:
                st.download_button(
                    "📥 Download Study Plan (.md)",
                    data=st.session_state.study_plan,
                    file_name=f"StudyPlan_{st.session_state.exam_target[:10]}_{days}Days.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with st.container(border=True):
                st.markdown(st.session_state.study_plan)
        else:
            st.info("Select your timeline and hours, then click **Generate Personalized Study Schedule**.")


# =====================================================
# 14. PERFORMANCE ANALYTICS
# =====================================================

elif selected_page == "📈 Performance Analytics":

    show_header(
        "Preparation Progress & Analytics",
        "Track mock test history, score progression, and accuracy over time."
    )

    history = st.session_state.quiz_history

    if not history:
        st.info("No mock test history found. Complete a quiz to view your performance analytics.")
        st.button(
            "📝 Take a Mock Test",
            use_container_width=True,
            on_click=navigate_to,
            args=("📝 Practice MCQs & Quiz",)
        )
    else:
        total_quizzes = len(history)
        avg_score = sum(h["percentage"] for h in history) / total_quizzes
        best_score = max(h["percentage"] for h in history)
        total_qs = sum(h["total"] for h in history)
        total_correct = sum(h["correct"] for h in history)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tests Attempted", total_quizzes)
        col2.metric("Average Score", f"{avg_score:.1f}%")
        col3.metric("Best Score", f"{best_score:.1f}%")
        col4.metric("Overall Accuracy", f"{(total_correct / total_qs * 100):.1f}%")

        st.divider()
        st.subheader("📜 Past Mock Test Attempts")

        # Display history table
        table_rows = []
        for idx, h in enumerate(reversed(history), 1):
            table_rows.append({
                "Attempt #": len(history) - idx + 1,
                "Date & Time": h.get("timestamp", "-"),
                "Exam": h.get("exam_type", "General"),
                "Score": f"{h['correct']}/{h['total']}",
                "Net Score": f"{h.get('net_score', h['correct']):.2f}",
                "Percentage": f"{h['percentage']:.1f}%"
            })

        st.dataframe(table_rows, use_container_width=True)


# =====================================================
# 15. EXPORT CENTER & STUDY NOTES
# =====================================================

elif selected_page == "📥 Export Center":

    show_header(
        "Study Notes & Export Center",
        "Download your customized revision sheets, question sets, and saved notes."
    )

    tab1, tab2 = st.tabs(["📝 My Saved Study Notes", "📦 Export Packages"])

    with tab1:
        notes = st.session_state.study_notes
        if not notes:
            st.info("You haven't saved any notes yet. While using 'Ask AI' or 'Topic Summary', click 'Save to Study Notes' to collect revision points here.")
        else:
            st.write(f"You have **{len(notes)}** saved notes:")
            for idx, note in enumerate(notes, 1):
                with st.expander(f"Note {idx}: {note['title']}"):
                    st.markdown(note["content"])
                    st.caption(f"Source: {note.get('source', '')}")

            # Download all notes combined
            all_notes_text = "\n\n---\n\n".join(
                f"# {n['title']}\n\n{n['content']}\n\n*Source: {n.get('source', '')}*"
                for n in notes
            )
            st.download_button(
                "📥 Download All Saved Notes (.md)",
                data=all_notes_text,
                file_name="My_Government_Exam_Notes.md",
                mime="text/markdown"
            )

    with tab2:
        st.markdown("### Export Full Study Pack")
        st.write("Download formatted revision notes and practice papers for offline study.")

        if st.session_state.quiz_result:
            quiz_export = export_quiz_to_markdown(
                st.session_state.quiz_result,
                document_name=st.session_state.document_name,
                exam_type=st.session_state.exam_target
            )
            st.download_button(
                "📥 Download Latest Mock Test Paper (.md)",
                data=quiz_export,
                file_name="Latest_Mock_Test_Paper.md",
                mime="text/markdown"
            )
        else:
            st.info("Complete a mock test to download practice papers with solutions.")


# =====================================================
# 16. FOOTER
# =====================================================

show_footer()
