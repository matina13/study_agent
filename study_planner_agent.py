#!/usr/bin/env python3
"""
Simple Study Planner Agent using LangChain
"""

import os
from dotenv import load_dotenv
import openai
from langchain.prompts import PromptTemplate


class StudyPlannerAgent:
    """Simple Study Planner Agent using LangChain concepts"""

    def __init__(self):
        """Initialize the agent"""
        load_dotenv()

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        # Set up OpenAI client for OpenRouter
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "deepseek/deepseek-chat-v3-0324:free"

        # Set up LangChain prompts
        self.setup_prompts()

        print("Study Planner Agent initialized with LangChain prompts")

    def setup_prompts(self):
        """Set up LangChain prompt templates"""

        self.study_plan_prompt = PromptTemplate(
            input_variables=["subject", "hours", "deadline", "focus_areas", "goals"],
            template="""Create a detailed study plan for:

Subject: {subject}
Available time: {hours} hours total
Deadline: {deadline}
Areas to focus on: {focus_areas}
Learning goals: {goals}

Please provide:
1. Daily breakdown with specific tasks tailored to the focus areas
2. Time allocation for each topic, prioritizing the focus areas
3. Recommended study methods for this subject and goals
4. Key milestones and checkpoints aligned with the learning goals
5. Tips for staying motivated and on track
6. How to measure progress toward the stated goals

Make it practical, achievable, and personalized to the focus areas and goals."""
        )

        self.study_methods_prompt = PromptTemplate(
            input_variables=["subject", "topic", "learning_style"],
            template="""Recommend the best study methods for:

Subject: {subject}
Specific topic: {topic}
Learning style: {learning_style}

Please provide:
1. Top 3 study techniques for this subject and topic
2. How to implement each technique specifically for this topic
3. Tools and resources needed
4. Common mistakes to avoid when studying this topic

Be specific and practical."""
        )

        self.topic_breakdown_prompt = PromptTemplate(
            input_variables=["subject", "topic", "difficulty"],
            template="""Break down this learning topic into manageable parts:

Subject: {subject}
Topic: {topic}
Difficulty level: {difficulty}

Please provide:
1. 5-7 subtopics in logical order
2. Estimated time for each subtopic
3. Prerequisites for each part
4. How each part builds on the previous one

Make it step-by-step and easy to follow."""
        )

    def call_ai(self, prompt: str) -> str:
        """Helper method to call the AI with formatted prompt"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            print(f"Error calling AI: {error_msg}")
            return error_msg

    def save_to_file(self, content: str, filename_prefix: str) -> str:
        """Save content to a file"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            return filename
        except Exception as e:
            print(f"Error saving file: {e}")
            return None

    def create_study_plan(self):
        """Interactive method to create a study plan with user input"""
        print("\nLet's create your personalized study plan!")
        subject = input("What subject do you want to study? ").strip()
        hours = input("How many total hours do you have available? ").strip()
        deadline = input("When is your deadline? (e.g., 'in 2 weeks', 'next Monday'): ").strip()
        focus_areas = input("Any specific areas to focus on? (Press Enter to skip): ").strip()
        goals = input("Any particular learning goals? (Press Enter to skip): ").strip()

        # Use default values if focus areas or goals are empty
        if not focus_areas:
            focus_areas = "General understanding of the subject"
        if not goals:
            goals = "Build solid foundation and practical skills"

        print(f"\nCreating your study plan ({hours} hours)...")

        # Format the prompt using LangChain PromptTemplate
        formatted_prompt = self.study_plan_prompt.format(
            subject=subject,
            hours=hours,
            deadline=deadline,
            focus_areas=focus_areas,
            goals=goals
        )

        # Call the AI with the formatted prompt
        plan = self.call_ai(formatted_prompt)

        print("\n" + "=" * 60)
        print("YOUR PERSONALIZED STUDY PLAN")
        print("=" * 60)
        print(plan)
        print("=" * 60)

        # Option to save the plan
        save_option = input("\nWould you like to save this study plan to a file? (y/n): ").lower().strip()
        if save_option == 'y':
            filename = self.save_to_file(plan, "study_plan")
            if filename:
                print(f"Study plan saved to: {filename}")
            else:
                print("Failed to save study plan")

        return plan

    def get_study_method_advice(self):
        """Get study method advice using LangChain prompt with user input"""
        print("\nLet's get personalized study method advice!")
        subject = input("What subject do you want study method advice for? ").strip()
        topic = input("Any specific topic within this subject? (Press Enter to skip): ").strip()
        learning_style = input("What is your learning style? (visual, auditory, kinesthetic, mixed): ").strip()

        # Use default if topic is empty
        if not topic:
            topic = "general concepts"

        print(f"\nGenerating study method advice...")

        # Format the prompt using LangChain PromptTemplate
        formatted_prompt = self.study_methods_prompt.format(
            subject=subject,
            topic=topic,
            learning_style=learning_style
        )

        # Call the AI with the formatted prompt
        advice = self.call_ai(formatted_prompt)

        print("\n" + "=" * 50)
        print("STUDY METHOD ADVICE")
        print("=" * 50)
        print(advice)
        print("=" * 50)

        # Option to save the advice
        save_option = input("\nWould you like to save this advice to a file? (y/n): ").lower().strip()
        if save_option == 'y':
            filename = self.save_to_file(advice, "study_methods")
            if filename:
                print(f"Study methods saved to: {filename}")
            else:
                print("Failed to save study methods")

        return advice

    def break_down_topic(self):
        """Break down a topic using LangChain prompt with user input"""
        print("\nLet's break down a complex topic!")
        subject = input("What subject is this topic in? ").strip()
        topic = input("Which topic would you like to break down? ").strip()
        difficulty = input("What's the difficulty level? (beginner, intermediate, advanced): ").strip()

        print(f"\nBreaking down {topic}...")

        # Format the prompt using LangChain PromptTemplate
        formatted_prompt = self.topic_breakdown_prompt.format(
            subject=subject,
            topic=topic,
            difficulty=difficulty
        )

        # Call the AI with the formatted prompt
        breakdown = self.call_ai(formatted_prompt)

        print("\n" + "=" * 50)
        print("TOPIC BREAKDOWN")
        print("=" * 50)
        print(breakdown)
        print("=" * 50)

        # Option to save the breakdown
        save_option = input("\nWould you like to save this breakdown to a file? (y/n): ").lower().strip()
        if save_option == 'y':
            filename = self.save_to_file(breakdown, "topic_breakdown")
            if filename:
                print(f"Topic breakdown saved to: {filename}")
            else:
                print("Failed to save topic breakdown")

        return breakdown


if __name__ == "__main__":
    print("Study Planner Agent module loaded successfully")