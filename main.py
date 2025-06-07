#!/usr/bin/env python3
"""
Ultra Simple 2-Agent Terminal Interface
"""

import os
from study_planner_agent import StudyPlannerAgent
from content_processor_agent import ContentProcessorAgent


def main():
    # Initialize agents
    print("Starting 2-Agent System...")
    study_planner = StudyPlannerAgent()
    content_processor = ContentProcessorAgent()
    study_planner.register_content_processor(content_processor)

    while True:
        print("\n" + "=" * 40)
        print("2-AGENT STUDY SYSTEM")
        print("=" * 40)
        print("1. Study Plan")
        print("2. Process File")
        print("3. Comprehensive Planning")
        print("4. Agent Chat")
        print("5. Exit")
        print("=" * 40)

        choice = input("Choose (1-5): ")

        if choice == '1':
            print("\nSTUDY PLAN")
            subject = input("Subject: ")
            hours = input("Hours: ")
            deadline = input("Deadline: ")

            if subject and hours and deadline:
                result = study_planner.create_plan(subject, hours, deadline, "General", "Master subject")
                print(f"\n{result}")
            else:
                print("Fill all fields")

        elif choice == '2':
            print("\nFILE PROCESSING")
            file_path = input("File path: ")

            if os.path.exists(file_path):
                print("Choose: (1) Summary (2) Notes (3) Study Plan from File")
                sub_choice = input("Choose: ")

                if sub_choice == '1':
                    result = content_processor.create_summary(file_path, "detailed", "medium")
                elif sub_choice == '2':
                    result = content_processor.create_notes(file_path, "detailed")
                elif sub_choice == '3':
                    hours = input("Hours available: ")
                    deadline = input("Deadline: ")
                    if hours and deadline:
                        result = content_processor.create_plan_from_processed_file(hours, deadline)
                    else:
                        result = "Need hours and deadline"
                else:
                    result = "Invalid choice"

                print(f"\n{result}")
            else:
                print("File not found")

        elif choice == '3':
            print("\nCOMPREHENSIVE PLANNING")
            subject = input("Subject: ")
            hours = input("Hours: ")
            deadline = input("Deadline: ")

            # Optional files
            files = []
            print("Add files? (y/n):", end=" ")
            if input().lower() == 'y':
                while True:
                    file_path = input("File path (or 'done'): ")
                    if file_path.lower() == 'done':
                        break
                    if os.path.exists(file_path):
                        files.append(file_path)
                        print(f"Added: {file_path}")

            if subject and hours and deadline:
                print("Agents working...")
                result = study_planner.comprehensive_planning(subject, hours, deadline, "General", "Master subject",
                                                              files)
                print(result)
            else:
                print("Fill all fields")


        elif choice == '5':
            print("Goodbye!")
            break

        else:
            print("Choose 1-5")

        input("\nPress Enter...")


if __name__ == "__main__":
    main()