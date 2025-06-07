#!/usr/bin/env python3
"""
Study Planner Agent
"""

from base_agent import BaseAgent


class StudyPlannerAgent(BaseAgent):
    """Handles study planning, methods, topic breakdown, and coordination"""

    def __init__(self):
        super().__init__("StudyPlanner")
        self.content_processor = None

    def register_content_processor(self, content_processor):
        """Register the content processor agent"""
        self.content_processor = content_processor
        print("🔗 ContentProcessor connected to StudyPlanner")

    def create_plan(self, subject: str, hours: str, deadline: str, focus: str, goals: str):
        """Create study plan with file context"""
        file_context = self._get_file_context()

        prompt = f"""Create study plan for {subject}. Hours: {hours}, Deadline: {deadline}
        Focus: {focus}, Goals: {goals}

        File Context: {file_context}

        Include:
        • Weekly schedule with hours per day
        • Daily study blocks
        • Weekly milestones
        • Study techniques
        • Review schedules

        Be specific and actionable."""

        result = self.call_ai(prompt, 1000)
        self.memory.store('current_plan', result)
        return result

    def get_methods(self, subject: str, topic: str, learning_style: str):
        """Get study methods with context"""
        file_context = self._get_file_context()

        prompt = f"""Best study methods for {subject}, topic: {topic}, style: {learning_style}

        File Context: {file_context}

        Include:
        • Top 3 techniques
        • Step-by-step instructions
        • Tools needed
        • How to measure success

        Make it practical."""

        return self.call_ai(prompt)

    def break_down_topic(self, subject: str, topic: str, difficulty: str):
        """Break down complex topic"""
        file_context = self._get_file_context()

        prompt = f"""Break down {subject} topic "{topic}" for {difficulty} learners

        File Context: {file_context}

        Include:
        • Prerequisites
        • 5-7 subtopics in order
        • For each: concepts, time, examples
        • Practice exercises

        Clear and organized."""

        return self.call_ai(prompt)

    def comprehensive_planning(self, subject: str, hours: str, deadline: str, focus: str, goals: str,
                               files: list = None):
        """Handle comprehensive planning with file processing"""
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
                except:
                    continue

            if file_insights:
                results.append("FILE ANALYSIS:\n" + "\n\n".join(file_insights))

        # Step 2: Create enhanced study plan
        self.send_message("ContentProcessor", "Creating enhanced plan with file context")
        plan = self.create_plan(subject, hours, deadline, focus, goals)
        results.append(f"STUDY PLAN:\n{plan}")

        # Step 3: Add strategic recommendations
        recommendations = self._get_recommendations(subject, plan)
        results.append(f"RECOMMENDATIONS:\n{recommendations}")

        # Step 4: Session summary
        comms = self.memory.get('communications')
        summary = f"""SESSION SUMMARY:
        • Files Processed: {len(self.memory.get('file_analyses'))}
        • Agent Communications: {len(comms)}
        • Enhanced Plan Created: Yes

        Recent Communications:"""

        for comm in comms[-5:]:
            summary += f"\n  • {comm['time']} - {comm['from']} → {comm['to']}: {comm['message']}"

        results.append(summary)

        return "\n\n" + "=" * 60 + "\n\n".join(results)

    def _get_file_context(self):
        """Get file analysis context"""
        analyses = self.memory.get('file_analyses')
        if not analyses:
            return "No file analysis available"

        context = []
        for file_path, analysis in analyses.items():
            context.append(f"{file_path}: {analysis}")

        return "\n".join(context) if context else "No file analysis available"

    def _get_recommendations(self, subject: str, plan: str):
        """Add strategic recommendations"""
        prompt = f"""Provide strategic study recommendations for {subject}:

        Plan: {plan[:1000]}

        Give:
        • Key success factors
        • Potential challenges
        • Optimization tips
        • Resource suggestions

        Keep concise and actionable."""

        return self.call_ai(prompt)

    def show_communications(self):
        """Show agent communications"""
        comms = self.memory.get('communications')
        print(f"\n📞 Communications ({len(comms)}):")
        for comm in comms[-10:]:
            print(f"{comm['time']} | {comm['from']} → {comm['to']}: {comm['message']}")