class Student:
    """
    Represents the student's state, including their
    observable history and latent knowledge state.
    """
    def __init__(self, student_id, latent_dim_d=32): # Added student_id
        """
        Initializes a new student.
        """
        self.student_id = student_id
        self.latent_dim_d = latent_dim_d # Keep track of expected state dimension
        self.history = []
        self.state = {} # The knowledge state vector (e.g., mastery scores)
        print(f"  [Student] Initialized for student {student_id}.")

    def update_history(self, question_id, is_correct, response_time_ms):
        """
        Adds a new interaction to the student's history.
        """
        interaction = {
            "question_id": question_id,
            "is_correct": is_correct,
            "response_time_ms": response_time_ms,
            "timestamp": "..." # In a real app, use datetime.now()
        }
        self.history.append(interaction)
        print(f"  [Student] History updated with Q{question_id}: {is_correct} (Time: {response_time_ms}ms)")

    def get_history(self):
        """
        Returns the full interaction history.
        """
        return self.history

    def set_state(self, new_state):
        """
        Updates the student's latent knowledge state.
        Called by the Tutor after the Tracer runs.
        """
        self.state = new_state
        print("[Student] State updated.")

    def get_state(self):
        """
        Returns the current latent knowledge state.
        Used by the Policy.
        """
        return self.state
