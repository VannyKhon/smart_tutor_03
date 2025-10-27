class Tutor:
    """
    The main orchestrator. Connects all components (Policy, Tracer, etc.).
    Runs the main interaction loop.
    """
    def __init__(self, student, policy, tracer, content_manager):
        """
        Initializes the Tutor with its required components.
        Loads and sorts the concepts to be taught.
        """
        self.student = student
        self.policy = policy
        self.tracer = tracer
        self.content_manager = content_manager

        # --- Load and Sort Concepts ---
        concepts_data = self.content_manager.concepts # Assumes this holds the dict from knowledge.json
        concepts_list_from_json = concepts_data.get('concepts', [])
        
        if not concepts_list_from_json:
             print("  [Tutor] WARNING: No 'concepts' found in knowledge.json")

        # Sort concepts by their ID (e.g., "c1", "c2", ..., "c10")
        # We need a sort key that handles numbers correctly within the string
        def sort_key(concept):
            try:
                # Extract number part (e.g., "c1" -> 1)
                return int(concept.get('id', 'c0')[1:]) 
            except ValueError:
                return 0 # Default if ID format is unexpected
                
        self.concepts_to_teach = sorted(
            concepts_list_from_json, 
            key=sort_key
        )
        
        self.current_concept_index = 0
        print(f"  [Tutor] Initialized. Ready to teach {len(self.concepts_to_teach)} concepts.")

    def _get_current_concept(self):
        """Gets the concept dict the student is currently working on."""
        if 0 <= self.current_concept_index < len(self.concepts_to_teach):
            return self.concepts_to_teach[self.current_concept_index]
        return None

    def _get_next_action(self):
        """
        Asks the policy for the next action based on the student's state.
        Handles moving to the next concept if the policy signals completion.
        Returns: (action_type, content, current_concept_id) or (None, None, None) if finished.
        """
        current_concept = self._get_current_concept()
        if not current_concept:
            print("[Tutor] All concepts completed!")
            return ("mastery", {"message": "You have mastered all concepts!"}, None)

        current_concept_id = current_concept.get('id', None)
        if not current_concept_id:
             print("[Tutor] Error: Current concept has no ID.")
             # Failsafe: move to next concept if possible
             self.current_concept_index += 1
             return self._get_next_action()
             
        student_state = self.student.get_state()
        student_history = self.student.get_history()
        
        # Ask the policy for the next action for this concept
        action_type, content = self.policy.select_action(
            student_state, 
            student_history, 
            current_concept_id
        )
        
        # Check if the policy decided to end the concept
        if action_type == "end_concept":
            print(f"  [Tutor] Policy signaled end of concept {current_concept_id}. Moving to next.")
            self.current_concept_index += 1
            # Recursively call to get the first action of the *new* concept
            return self._get_next_action()

        # Return the chosen action and the ID of the concept it belongs to
        return (action_type, content, current_concept_id)

    def start_session(self):
        """
        Called by app.py to start the tutoring session.
        Resets progress and gets the first action.
        """
        print("[Tutor] Session started.")
        self.current_concept_index = 0 # Start from the first concept
        return self._get_next_action()

    def submit_answer(self, question_id, user_answer, response_time_ms):
        """
        Called by app.py when the user submits an answer.
        1. Grade the answer.
        2. Update student history.
        3. Update student knowledge state (via tracer).
        4. Get the next action (via policy).
        Returns: (action_type, content, current_concept_id)
        """
        print(f"[Tutor] Received answer for Q{question_id}: '{user_answer}' (Time: {response_time_ms}ms)")
        
        # 1. Get the correct question/answer for grading
        question = self.content_manager.get_question(question_id)
        if not question:
            print(f"  [Tutor] ERROR: Could not find question {question_id} to grade.")
            # Failsafe: Try to get the next action anyway
            return self._get_next_action()
            
        correct_answer = str(question.get('answer', '')) # Default to empty string if missing
        
        # 2. Grade the user's answer (case-insensitive string comparison)
        is_correct = (str(user_answer).lower() == correct_answer.lower())
        print(f"  [Tutor] User answer: '{user_answer}', Correct answer: '{correct_answer}', Graded: {is_correct}")
        
        # 3. Update student history
        self.student.update_history(question_id, is_correct, response_time_ms)
        
        # 4. Update knowledge state (call the tracer)
        history = self.student.get_history()
        new_state = self.tracer.update_state(history)
        self.student.set_state(new_state) # Save the new state
        
        # 5. Get next action from the policy
        return self._get_next_action()
