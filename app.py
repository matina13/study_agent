#!/usr/bin/env python3
import streamlit as st
import tempfile
import os
from datetime import datetime

from SQLiteState import *
from study_planner_agent import StudyPlannerAgent
from content_processor_agent import ContentProcessorAgent

st.set_page_config(page_title="Study System", layout="wide")


@st.cache_resource
def get_agents():
    planner = StudyPlannerAgent()
    processor = ContentProcessorAgent()
    planner.register_content_processor(processor)
    return planner, processor


planner, processor = get_agents()

# User setup with name login
if 'user_id' not in st.session_state:
    username = st.text_input("👤 Enter your name to continue:", placeholder="e.g.,  Giannis  ")
    if username:
        import hashlib
        user_id = hashlib.md5(username.lower().strip().encode()).hexdigest()[:16]
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.rerun()
    else:
        st.info("Please enter your name to use the study system")
        st.stop()

user_id = st.session_state.user_id

# Re-set user context on every run (important for memory mode)
planner.set_user(user_id)
processor.set_user(user_id)

st.title("Study System")

# Sidebar
with st.sidebar:
    st.header("👤 Profile")

    user = get_user(user_id)

    # Learning style selector
    current_style = user.get('style', 'visual')
    style_options = ["visual", "auditory", "reading", "custom"]

    if current_style not in style_options:
        # If user has a custom style, show it as selected
        selected_index = 3  # custom
    else:
        selected_index = style_options.index(current_style)

    style = st.selectbox(
        "Learning Style",
        style_options,
        index=selected_index
    )

    if style == "custom":
        custom_style = st.text_input("Custom Style", value=current_style if current_style not in ["visual", "auditory",
                                                                                                  "reading"] else "")
        if custom_style and custom_style != current_style:
            user['style'] = custom_style
            state.set(f"user:{user_id}", user)
            st.rerun()
    elif style != current_style:
        user['style'] = style
        state.set(f"user:{user_id}", user)
        st.rerun()

    st.write(f"**User:** {st.session_state.get('username', 'Unknown')}")
    st.write(f"**ID:** {user_id[:8]}...")

    stats = get_analytics(user_id)

    if stats["subjects"]:
        st.subheader("📊 Recent Subjects")
        for subject in stats["subjects"][:3]:
            st.write(f"• {subject}")

    if stats["sessions"] > 0:
        st.subheader("📈 Quick Stats")
        st.write(f"**Sessions:** {stats['sessions']}")
        st.write(f"**Hours:** {stats['hours']}")

# Main interface
tab1, tab2, tab3 = st.tabs(["📚 Study Planning", "📄 File Processing", "📝 Content Library"])

with tab1:
    st.header("Create Study Plan")

    # Basic fields
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject", placeholder="e.g., Python Programming, Calculus")
    with col2:
        topic = st.text_input("Specific Topic (optional)", placeholder="e.g., Machine Learning, Derivatives")

    col3, col4, col5 = st.columns(3)
    with col3:
        hours = st.text_input("Hours", placeholder="e.g., 20 hours")
    with col4:
        deadline = st.text_input("Deadline", placeholder="e.g., Dec 15, 2025")
    with col5:
        daily_time = st.text_input("Daily Time (optional)", placeholder="e.g., 2 hours")

    goals = st.text_area("Learning Goals (optional)", placeholder="What do you want to achieve?", height=80)

    col6, col7 = st.columns(2)
    with col6:
        difficulty = st.selectbox("Current Level", ["Beginner", "Intermediate", "Advanced"], index=1)
    with col7:
        focus = st.text_input("Focus Areas (optional)", placeholder="e.g., Problem solving, Theory")

    if st.button("🎯 Create Study Plan", type="primary", use_container_width=True) and subject and hours and deadline:
        with st.spinner("Creating your study plan..."):
            session_id = start_session(user_id, subject)

            # Enhanced prompt with additional fields
            enhanced_focus = f"{focus}, {topic}" if focus and topic else (focus or topic or "General")
            enhanced_goals = f"{goals}. Level: {difficulty}. Daily time: {daily_time or 'flexible'}."

            result = planner.create_plan(subject, hours, deadline, enhanced_focus, enhanced_goals)
            end_session(session_id)

        st.success("✅ Study plan created!")
        st.markdown("### 🎯 Your Study Plan")
        st.markdown(result)
        st.download_button("📥 Download", result, f"plan_{datetime.now().strftime('%m%d_%H%M')}.txt",
                           use_container_width=True)

with tab2:
    st.header("Process Files")

    file = st.file_uploader("📁 Upload file", type=['pdf', 'txt', 'docx'])

    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as tmp:
            tmp.write(file.getvalue())
            path = tmp.name

        col1, col2, col3 = st.columns(3)

        if 'result' not in st.session_state:
            st.session_state.result = None

        with col1:
            if st.button("📋 Summary", use_container_width=True):
                session_id = start_session(user_id, "Processing")
                st.session_state.result = processor.create_summary(path, "detailed", "medium", file.name)
                end_session(session_id)

        with col2:
            if st.button("📝 Notes", use_container_width=True):
                session_id = start_session(user_id, "Processing")
                st.session_state.result = processor.create_notes(path, "detailed", file.name)
                end_session(session_id)

        with col3:
            if st.button("❓ Questions", use_container_width=True):
                session_id = start_session(user_id, "Processing")
                st.session_state.result = processor.create_questions(path, "mixed", "medium", file.name)
                end_session(session_id)

        if st.session_state.result:
            st.markdown("---")
            st.markdown(st.session_state.result)
            st.download_button("📥 Download", st.session_state.result,
                               f"content_{datetime.now().strftime('%m%d_%H%M')}.txt")

        # File-based plan
        st.markdown("---")
        st.subheader("📅 Create Plan from File")
        col4, col5 = st.columns(2)
        with col4:
            plan_hours = st.text_input("Study Hours")
        with col5:
            plan_deadline = st.text_input("Study Deadline")

        if st.button("📋 Plan from File", use_container_width=True) and plan_hours and plan_deadline:
            session_id = start_session(user_id, "File Planning")
            result = processor.create_plan_from_processed_file(plan_hours, plan_deadline)
            end_session(session_id)
            st.markdown("### 📋 File-Based Plan")
            st.markdown(result)
            st.download_button("📥 Download Plan", result,
                               f"file_plan_{datetime.now().strftime('%m%d_%H%M')}.txt",
                               use_container_width=True)

        os.unlink(path)

with tab3:
    st.header("Your Library")

    content = get_user_content(user_id, 50)

    if content:
        # Group content by filename
        files = {}
        for item in content:
            filename = item['filename']
            if filename not in files:
                files[filename] = []
            files[filename].append(item)

        # Display each file and its content
        for filename, items in files.items():
            with st.expander(f"📄 {filename} ({len(items)} items)"):
                for item in items:
                    st.markdown(f"**{item['type'].title()}** - {item['created'][:16]}")
                    st.write(item['content'][:150] + "..." if len(item['content']) > 150 else item['content'])
                    st.download_button(f"Download {item['type']}", item['content'],
                                       f"{item['type']}_{filename}_{item['created'][:10]}.txt",
                                       key=item['id'])
                    st.markdown("---")
    else:
        st.info("No content saved yet. Process some files to build your library!")