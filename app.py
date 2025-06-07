import streamlit as st
import tempfile
import os
from datetime import datetime
from study_planner_agent import StudyPlannerAgent
from content_processor_agent import ContentProcessorAgent


# Initialize agents once
@st.cache_resource
def get_agents():
    study_planner = StudyPlannerAgent()
    content_processor = ContentProcessorAgent()
    study_planner.register_content_processor(content_processor)
    return study_planner, content_processor


study_planner, content_processor = get_agents()

st.set_page_config(page_title="2-Agent Study System", layout="wide")
st.title("Multy-Agent Study System")
st.caption("StudyPlanner + ContentProcessor working together")

# Tabs
tab1, tab2 = st.tabs(["Study Planning", "File Processing"])

with tab1:
    st.header("Study Planning")

    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject", key="plan_subject", placeholder="e.g., Mathematics, Python")
        hours = st.text_input("Hours Available", key="plan_hours", placeholder="e.g., 20, 40")
    with col2:
        deadline = st.text_input("Deadline", key="plan_deadline", placeholder="e.g., 2 weeks, Dec 15")
        focus = st.text_input("Focus Areas", key="plan_focus", placeholder="Optional: specific topics")

    goals = st.text_area("Learning Goals", key="plan_goals", placeholder="Optional: what you want to achieve")

    # Upload study materials
    uploaded_files = st.file_uploader(
        "Upload study materials (optional)",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload materials to enhance your study plan"
    )

    if st.button("Create Study Plan", use_container_width=True):
        if subject and hours and deadline:
            with st.spinner("Creating your study plan..."):
                # Process files if uploaded
                file_paths = []
                if uploaded_files:
                    for file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as tmp:
                            tmp.write(file.getvalue())
                            file_paths.append(tmp.name)

                # Create comprehensive plan with files
                if file_paths:
                    result = study_planner.comprehensive_planning(
                        subject, hours, deadline,
                        focus or "General understanding",
                        goals or "Master the subject",
                        file_paths
                    )
                else:
                    result = study_planner.create_plan(
                        subject, hours, deadline,
                        focus or "General understanding",
                        goals or "Master the subject"
                    )

                st.success("Study plan created!")
                st.markdown("### Your Study Plan")
                with st.container():
                    st.markdown(f"```\n{result}\n```")

                # Download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    "Download Study Plan",
                    result,
                    f"study_plan_{subject.replace(' ', '_')}_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

                # Cleanup
                for path in file_paths:
                    try:
                        os.unlink(path)
                    except:
                        pass
        else:
            st.error("Please fill in Subject, Hours, and Deadline")

with tab2:
    st.header("File Processing")

    uploaded_file = st.file_uploader(
        "Upload your study material",
        type=['pdf', 'docx', 'txt'],
        help="Supported: PDF, Word documents, text files"
    )

    if uploaded_file:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        st.success(f"File uploaded: {uploaded_file.name}")

        # Processing options
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Create Summary", use_container_width=True):
                with st.spinner("Creating summary..."):
                    result = content_processor.create_summary(tmp_path, "detailed", "medium")

                    st.markdown("### Summary")
                    with st.container():
                        st.markdown(result)

                    # Download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download Summary",
                        result,
                        f"summary_{uploaded_file.name}_{timestamp}.txt",
                        mime="text/plain"
                    )

        with col2:
            if st.button("Create Notes", use_container_width=True):
                with st.spinner("Creating study notes..."):
                    result = content_processor.create_notes(tmp_path, "detailed")

                    st.markdown("### Study Notes")
                    with st.container():
                        st.markdown(result)

                    # Download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download Notes",
                        result,
                        f"notes_{uploaded_file.name}_{timestamp}.txt",
                        mime="text/plain"
                    )

        with col3:
            if st.button("Generate Questions", use_container_width=True):
                with st.spinner("Generating questions..."):
                    result = content_processor.create_questions(tmp_path, "mixed", "medium")

                    st.markdown("### Practice Questions")
                    with st.container():
                        st.markdown(result)

                    # Download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download Questions",
                        result,
                        f"questions_{uploaded_file.name}_{timestamp}.txt",
                        mime="text/plain"
                    )

        # Study plan from file
        st.markdown("---")
        st.subheader("Create Study Plan from This File")
        st.caption("Generate a study plan specifically for this material")

        col4, col5 = st.columns(2)
        with col4:
            file_hours = st.text_input("Hours Available", key="file_hours", placeholder="e.g., 15, 30")
        with col5:
            file_deadline = st.text_input("Deadline", key="file_deadline", placeholder="e.g., 1 week, Nov 30")

        if st.button("Create Plan from File", use_container_width=True):
            if file_hours and file_deadline:
                with st.spinner("Creating file-specific study plan..."):
                    result = content_processor.create_plan_from_processed_file(file_hours, file_deadline)

                    st.markdown("### Study Plan for This File")
                    with st.container():
                        st.markdown(f"```\n{result}\n```")

                    # Download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download File-Based Plan",
                        result,
                        f"file_plan_{uploaded_file.name}_{timestamp}.txt",
                        mime="text/plain"
                    )
            else:
                st.error("Please enter both hours and deadline")

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

# Sidebar status
with st.sidebar:
    st.markdown("### System Status")
    st.success("2 Agents Active")
    st.markdown("**StudyPlanner**: Plans, methods, coordination")
    st.markdown("**ContentProcessor**: Files, summaries, notes")

    # Show file analyses count
    analyses = study_planner.memory.get('file_analyses')
    file_count = len(analyses) if analyses else 0
    st.metric("Files Processed", file_count)