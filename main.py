#!/usr/bin/env python3
"""
Main application using Study Planner Agent
"""

import os
from dotenv import load_dotenv
import openai
from study_planner_agent import StudyPlannerAgent


def test_api():
    """Test the DeepSeek API connection"""

    # Load environment variables from .env file
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("ERROR: No API key found!")
        print("Make sure your .env file has: OPENROUTER_API_KEY=your_key_here")
        return False

    print(f"Found API key: {api_key[:15]}...")

    try:
        # Set up OpenAI client to use OpenRouter
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        print("Testing DeepSeek connection...")

        # Simple test message
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=50
        )

        result = response.choices[0].message.content
        print(f"SUCCESS! DeepSeek replied: {result}")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def show_menu():
    """Show the main menu"""
    print("\n=== Study Planner Assistant ===")
    print("1. Test API Connection")
    print("2. Create Study Plan")
    print("3. Get Study Method Advice")
    print("4. Break Down Topic")
    print("5. Exit")
    print("================================")


def main():
    """Main function"""
    print("Welcome to your Study Planner Assistant!")

    # Initialize agent once
    try:
        agent = StudyPlannerAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    while True:
        show_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            print("\n=== Testing API Connection ===")
            if test_api():
                print("API test passed!")
            else:
                print("API test failed!")

        elif choice == "2":
            agent.create_study_plan()

        elif choice == "3":
            agent.get_study_method_advice()

        elif choice == "4":
            agent.break_down_topic()

        elif choice == "5":
            print("Goodbye! Happy studying!")
            break

        else:
            print("Invalid choice. Please enter 1-5.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()