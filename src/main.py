import sys
import questionary
from database import Database, setup_tables, seed_db
from habit import Habit
import analytics

class CLI:
    """
    The primary controller for the application.
    Bridges the interactive terminal interface with the underlying 
    Object-Oriented (Habit) and Functional (Analytics) backend logic.
    """
    def __init__(self):
        # Initialize the persistence layer and prepare the environment
        self.db = Database("habits.db")
        setup_tables(self.db)
        seed_db(self.db)

    # =====================================================================
    # CORE INTERFACE METHODS
    # =====================================================================

    def get_user_input(self, prompt_type, message, choices=None):
        """
        Centralized input handler leveraging the Questionary library.
        Ensures all user prompts are visually standardized and safely catches 
        keyboard interrupts (Ctrl+C) to prevent ugly terminal crashes.
        """
        try:
            if prompt_type == 'select':
                return questionary.select(message, choices=choices).ask()
            elif prompt_type == 'text':
                return questionary.text(message).ask()
        except KeyboardInterrupt:
            print("\nExiting application...")
            sys.exit(0)

    def run_menu(self):
        """
        The main application execution loop. 
        Renders the interactive menu and routes the user's selection 
        to the appropriate internal backend handler.
        """
        print("\n=== HABIT TRACKER INITIALIZED ===")
        
        while True:
            choice = self.get_user_input(
                'select',
                "Main Menu: What would you like to do?",
                choices=[
                    "1. Create a new habit",
                    "2. Check-off a habit",
                    "3. Delete a habit",
                    "4. Analytics Menu",
                    "5. Exit"
                ]
            )

            # Handle graceful exit if user selects Exit or interrupts the prompt
            if choice is None or choice == "5. Exit":
                print("Shutting down... Goodbye!")
                break

            # Route the selection to the designated private handler
            if choice == "1. Create a new habit":
                self._handle_create()
            elif choice == "2. Check-off a habit":
                self._handle_checkoff()
            elif choice == "3. Delete a habit":
                self._handle_delete()
            elif choice == "4. Analytics Menu":
                self._handle_analytics()

    # =====================================================================
    # INTERNAL HANDLERS
    # Encapsulates the specific logic for each menu option to keep the 
    # main run_menu() loop clean and readable.
    # =====================================================================

    def _get_active_habit_names(self):
        """Helper function to dynamically populate dropdown menus with existing habits."""
        habits = analytics.return_all_habits(self.db)
        return [h[0] for h in habits] if habits else []

    def _handle_create(self):
        name = self.get_user_input('text', "Enter the name of your new habit:")
        if not name or name.strip() == "":
            print("[!] Habit name cannot be empty.\n")
            return
            
        periodicity = self.get_user_input('select', "Select periodicity:", choices=["Daily", "Weekly"])
        
        # Instantiate a new Habit object and persist it to the database
        new_habit = Habit(name.strip(), periodicity, self.db)
        if new_habit.store():
            print(f"[+] Successfully created habit: {name}\n")

    def _handle_checkoff(self):
        habit_names = self._get_active_habit_names()
        if not habit_names:
            print("[!] No habits found. Please create one first.\n")
            return
            
        target = self.get_user_input('select', "Which habit did you complete?", choices=habit_names)
        if target:
            # Reconstruct the habit in memory to utilize its OOP methods
            h = Habit(target, "Unknown", self.db) 
            if h.check_off():
                print(f"[+] Successfully checked off: {target}\n")

    def _handle_delete(self):
        habit_names = self._get_active_habit_names()
        if not habit_names:
            print("[!] No habits found.\n")
            return
            
        target = self.get_user_input('select', "Which habit do you want to delete?", choices=habit_names)
        if target:
            confirm = self.get_user_input('select', f"Are you sure you want to delete '{target}'?", choices=["No", "Yes"])
            if confirm == "Yes":
                h = Habit(target, "Unknown", self.db)
                if h.delete():
                    print(f"[-] Successfully deleted: {target}\n")

    def _handle_analytics(self):
        """Renders a dedicated submenu for querying the functional analytics engine."""
        while True:
            choice = self.get_user_input(
                'select',
                "Analytics Menu:",
                choices=[
                    "1. View all currently tracked habits",
                    "2. View habits by periodicity",
                    "3. View longest streak for a specific habit",
                    "4. View longest streak across all habits",
                    "5. Return to Main Menu"
                ]
            )

            if choice is None or choice == "5. Return to Main Menu":
                print("") # Print a newline for visual spacing
                break
                
            if choice == "1. View all currently tracked habits":
                habits = analytics.return_all_habits(self.db)
                print("\n--- All Habits ---")
                for h in habits:
                    print(f"- {h[0]} ({h[1]}) | Created: {h[2]}")
                print("------------------\n")

            elif choice == "2. View habits by periodicity":
                periodicity = self.get_user_input('select', "Select periodicity:", choices=["Daily", "Weekly"])
                habits = analytics.return_habits_by_periodicity(self.db, periodicity)
                print(f"\n--- {periodicity} Habits ---")
                for h in habits:
                    print(f"- {h[0]}")
                print("--------------------\n")

            elif choice == "3. View longest streak for a specific habit":
                habit_names = self._get_active_habit_names()
                if not habit_names:
                    print("[!] No habits found.\n")
                    continue
                    
                target = self.get_user_input('select', "Select a habit:", choices=habit_names)
                if target:
                    # Dynamically fetch the periodicity required for the reducer function
                    all_h = analytics.return_all_habits(self.db)
                    periodicity = next((h[1] for h in all_h if h[0] == target), 'daily')
                    
                    streak = analytics.return_longest_streak_for_habit(self.db, target, periodicity)
                    print(f"\n[*] The longest streak for '{target}' is {streak}.\n")

            elif choice == "4. View longest streak across all habits":
                best_habit, streak = analytics.return_longest_streak_all(self.db)
                print(f"\n[*] The longest overall streak belongs to '{best_habit}' with {streak} completions.\n")

# =====================================================================
# EXECUTION ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    app = CLI()
    app.run_menu()