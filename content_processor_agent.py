# content_processor_agent.py
import os
from pathlib import Path
import PyPDF2
import docx
from base_agent import BaseAgent
from RedisState import state, save_content


class ContentProcessorAgent(BaseAgent):
    """Minimal optimized file processing with Redis state"""

    def __init__(self):
        super().__init__("ContentProcessor")
        self.file_cache = {}

    def read_file(self, file_path: str):
        """Read and cache file content"""
        if file_path in self.file_cache:
            return self.file_cache[file_path]

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

            self.file_cache[file_path] = content

            # Auto-analyze and save
            if self.current_user_id:
                analysis = self.analyze_for_planning(content, file_path)
                save_content(self.current_user_id, Path(file_path).name, "file_analysis", analysis)

            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def analyze_for_planning(self, content: str, filename: str):
        """Quick content analysis"""
        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}

        prompt = f"""Analyze for study planning:
File: {Path(filename).name}
Style: {user.get('style', 'visual')}
Content: {content[:1500]}

Provide: subject, key concepts, difficulty, study time, focus areas."""

        return self.call_ai(prompt, 400)

    def create_summary(self, file_path: str, summary_type: str = "detailed", length: str = "medium",
                       original_filename: str = None):
        """Create summary"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}

        prompt = f"Create a {length} summary for a {user.get('style', 'visual')} learner:\n{content[:3000]}"
        result = self.call_ai(prompt, 800)

        if self.current_user_id:
            filename = original_filename or Path(file_path).name
            save_content(self.current_user_id, filename, "summary", result)

        return result

    def create_notes(self, file_path: str, note_style: str = "detailed", original_filename: str = None):
        """Create notes"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}

        prompt = f"Create study notes for a {user.get('style', 'visual')} learner:\n{content[:3000]}\n\nInclude main topics, key facts, and review questions."
        result = self.call_ai(prompt, 800)

        if self.current_user_id:
            filename = original_filename or Path(file_path).name
            save_content(self.current_user_id, filename, "notes", result)

        return result

    def create_questions(self, file_path: str, question_type: str = "mixed", difficulty: str = "medium",
                         original_filename: str = None):
        """Generate questions"""
        content = self.read_file(file_path)
        if content.startswith("Error"):
            return content

        user = state.get(f"user:{self.current_user_id}", {}) if self.current_user_id else {}

        prompt = f"Generate {difficulty} questions for a {user.get('style', 'visual')} learner:\n{content[:3000]}\n\nInclude recall, comprehension, and application questions with answers."
        result = self.call_ai(prompt, 800)

        if self.current_user_id:
            filename = original_filename or Path(file_path).name
            save_content(self.current_user_id, filename, "questions", result)

        return result

    def create_plan_from_processed_file(self, hours: str, deadline: str):
        """Create study plan from processed content"""
        if not self.current_user_id:
            return "No user context available. Please set user first."

        user_content = state.get_list(f"user_content:{self.current_user_id}", 10)
        if not user_content:
            return "No files processed yet. Please process a file first."

        # Get content for latest file
        latest_file = user_content[0]['filename']
        file_content = [f"{item['type'].upper()}: {item['content']}"
                        for item in user_content if item['filename'] == latest_file]

        if not file_content:
            return "No processed content found for this file."

        user = state.get(f"user:{self.current_user_id}", {})
        combined_content = "\n\n".join(file_content)

        prompt = f"""Create study plan:
File: {latest_file}
Hours: {hours}
Deadline: {deadline}
Style: {user.get('style', 'visual')}

CONTENT:
{combined_content[:2000]}

Create a plan that uses the content above, breaks down {hours} hours until {deadline}, and matches {user.get('style', 'visual')} learning."""

        result = self.call_ai(prompt, 1000)

        if self.current_user_id:
            save_content(self.current_user_id, f"Study Plan - {latest_file}", "study_plan", result)

        return result

