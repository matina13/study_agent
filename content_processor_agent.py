import os
from pathlib import Path
import PyPDF2
import docx
from base_agent import BaseAgent


class ContentProcessorAgent(BaseAgent):
    """Handles file processing and content analysis"""

    def __init__(self):
        super().__init__("ContentProcessor")

    def read_file(self, file_path: str):
        """Read file and auto-analyze"""
        ext = Path(file_path).suffix.lower()

        try:
            if ext == '.pdf':
                with open(file_path, 'rb') as f:
                    content = "\n".join([page.extract_text() for page in PyPDF2.PdfReader(f).pages])
            elif ext in ['.docx', '.doc']:
                content = "\n".join([p.text for p in docx.Document(file_path).paragraphs])
            elif ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                return f"Unsupported file: {ext}"

            # Auto-analyze for study planning
            analysis = self.analyze_for_planning(content, file_path)

            # Store analysis
            current_analyses = self.memory.get('file_analyses')
            current_analyses[file_path] = analysis
            self.memory.store('file_analyses', current_analyses)

            self.send_message("StudyPlanner", "File analyzed")
            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def analyze_for_planning(self, content: str, filename: str):
        """Analyze content for study planning"""
        prompt = f"""Analyze for study planning:

        File: {Path(filename).name}
        Content: {content[:1500]}

        Provide:
        • Subject/topic
        • Key concepts
        • Difficulty level
        • Study time needed
        • Focus areas

        Keep concise."""

        return self.call_ai(prompt, 400)

    def create_summary(self, file_path: str, summary_type: str, length: str):
        """Create file summary"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        prompt = f"""Create {length} {summary_type} summary:
        {content[:3000]}

        Include key concepts, study focus areas, and study tips."""

        return self.call_ai(prompt, 800)

    def create_notes(self, file_path: str, note_style: str):
        """Create study notes"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        prompt = f"""Create {note_style} study notes:
        {content[:3000]}

        Include main topics, key information, and learning reinforcement."""

        return self.call_ai(prompt, 800)

    def create_questions(self, file_path: str, question_type: str, difficulty: str):
        """Generate questions"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        prompt = f"""Generate {difficulty} {question_type} questions:
        {content[:3000]}

        Include recall, comprehension, application questions with answers."""

        return self.call_ai(prompt, 800)

    def analyze_text(self, content: str):
        """Analyze direct text"""
        prompt = f"""Analyze for study:
        {content[:3000]}

        Provide:
        • Main themes
        • Key terms
        • Difficulty assessment
        • Study recommendations
        • Potential questions

        Be comprehensive."""

        result = self.call_ai(prompt)
        self.send_message("StudyPlanner", "Text analyzed")
        return result

    def create_plan_from_processed_file(self, hours: str, deadline: str):
        """Create study plan from most recently processed file"""

        # Get the most recent file analysis
        file_analyses = self.memory.get('file_analyses')
        if not file_analyses:
            return "No files have been processed yet. Please process a file first."

        # Get the last processed file
        latest_file = list(file_analyses.keys())[-1]
        latest_analysis = file_analyses[latest_file]

        # Extract subject from analysis or filename
        filename = Path(latest_file).stem

        prompt = f"""Create a study plan based on this processed file:

        File: {filename}
        Analysis: {latest_analysis}
        Hours Available: {hours}
        Deadline: {deadline}

        Create a detailed study plan that:
        • Uses the specific content from this file
        • Breaks down the {hours} hours across the timeline
        • Focuses on the key concepts identified in the analysis
        • Includes review schedules
        • Provides specific milestones

        Make it actionable and file-specific."""

        result = self.call_ai(prompt, 1000)

        # Store the plan and notify StudyPlanner
        self.memory.store('file_based_plan', result)
        self.send_message("StudyPlanner", f"Created study plan from {filename}")

        return result