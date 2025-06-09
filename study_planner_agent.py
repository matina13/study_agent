# study_planner_agent.py
# !/usr/bin/env python3
from base_agent import BaseAgent
from SQLiteState import *


class StudyPlannerAgent(BaseAgent):
    """Handles study planning with Redis state memory"""

    def __init__(self):
        super().__init__("StudyPlanner")
        self.content_processor = None

    def register_content_processor(self, content_processor):
        """Register the content processor agent"""
        self.content_processor = content_processor
        print("🔗 ContentProcessor connected to StudyPlanner")

    def create_plan(self, subject: str, hours: str, deadline: str, focus: str, goals: str):
        """Create study plan with user context from Redis"""

        # Get user context
        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}
        user_sessions = state.get_list(f"sessions:{self.current_user_id}", 5) if self.current_user_id else []

        # Build context from previous sessions
        session_context = ""
        if user_sessions:
            recent_subjects = [s.get('subject', '') for s in user_sessions]
            session_context = f"\nRecent study subjects: {', '.join(recent_subjects)}"

        prompt = f"""Create a personalized study plan for {subject}.

User Profile:
- Learning Style: {user.get('style', 'visual')}
- Hours Available: {hours}
- Deadline: {deadline}
- Focus Areas: {focus}
- Goals: {goals}
{session_context}

Create a detailed study plan with:
• Weekly schedule breakdown
• Daily study blocks with specific hours
• Study techniques suited to their learning style
• Weekly milestones and checkpoints
• Review schedules
• Specific actionable tasks

Make it personalized and realistic."""

        result = self.call_ai(prompt, 1000)

        # Save plan to Redis
        if self.current_user_id:
            save_content(self.current_user_id, f"Study Plan - {subject}", "plan", result)

        return result

    def get_methods(self, subject: str, topic: str, learning_style: str):
        """Get study methods with user context"""
        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}

        prompt = f"""Recommend study methods for {subject}, topic: {topic}

User Learning Style: {learning_style or user.get('style', 'visual')}

Provide:
• Top 3 techniques for this learning style
• Step-by-step instructions
• Tools and resources needed
• How to measure progress
• Time estimates

Make it practical and actionable."""

        return self.call_ai(prompt, 600)

    def comprehensive_planning(self, subject: str, hours: str, deadline: str, focus: str, goals: str,
                               files: list = None):
        """Handle comprehensive planning with file processing and Redis state"""
        print(f"\n🎯 Comprehensive planning for {subject}")

        results = []

        # Step 1: Process files if provided
        if files and self.content_processor:
            self.send_message("ContentProcessor", "Process files for comprehensive planning")
            file_insights = []

            for file_path in files:
                try:
                    content = self.content_processor.read_file(file_path)
                    if not content.startswith("Error"):
                        insight = self.content_processor.analyze_for_planning(content, file_path)
                        file_insights.append(f"📄 {file_path}: {insight}")

                        # Save file analysis to Redis
                        if self.current_user_id:
                            save_content(self.current_user_id, file_path, "analysis", insight)

                except Exception as e:
                    continue

            if file_insights:
                results.append("FILE ANALYSIS:\n" + "\n\n".join(file_insights))

        # Step 2: Create enhanced study plan
        self.send_message("ContentProcessor", "Creating enhanced plan with file context")
        plan = self.create_plan(subject, hours, deadline, focus, goals)
        results.append(f"STUDY PLAN:\n{plan}")

        # Step 3: Add strategic recommendations based on user history
        recommendations = self.get_recommendations(subject, plan)
        results.append(f"RECOMMENDATIONS:\n{recommendations}")

        # Step 4: Session summary from Redis
        user_sessions = state.get_list(f"sessions:{self.current_user_id}", 5) if self.current_user_id else []
        user_content = state.get_list(f"user_content:{self.current_user_id}", 5) if self.current_user_id else []

        summary = f"""SESSION SUMMARY:
• Files Processed: {len(files) if files else 0}
• Content Saved: {len(user_content)}
• Recent Sessions: {len(user_sessions)}
• Enhanced Plan Created: Yes

Recent Study Activity:"""

        for session in user_sessions[:3]:
            activities = len(session.get('activities', []))
            summary += f"\n  • {session.get('start', '')[:16]} - {session.get('subject', '')}: {activities} activities"

        results.append(summary)

        return "\n\n" + "=" * 60 + "\n\n".join(results)

    def get_recommendations(self, subject: str, plan: str):
        """Add strategic recommendations based on Redis data"""
        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}
        sessions = state.get_list(f"sessions:{self.current_user_id}", 10) if self.current_user_id else []

        # Analyze user patterns
        session_subjects = [s.get('subject', '') for s in sessions]
        study_frequency = len([s for s in sessions if s.get('end')])

        context = f"""User: {user.get('style', 'visual')} learner
Recent subjects: {', '.join(session_subjects[:3])}
Study frequency: {study_frequency} completed sessions
Current plan for: {subject}

Plan preview: {plan[:500]}"""

        prompt = f"""Based on this user's study history and learning style, provide strategic recommendations:

{context}

Give personalized advice on:
• Key success factors for this user
• Potential challenges based on their history
• Optimization tips for their learning style
• Resource suggestions
• Study schedule adjustments

Keep concise and actionable."""

        return self.call_ai(prompt, 500)