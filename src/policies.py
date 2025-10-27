import random

class SimpleDifficultyPolicy:
    """
    A simple heuristic policy.
    Selects the hardest unseen question for the current concept.
    Falls back to examples if no questions are left.
    """
    def __init__(self, question_bank, example_bank):
        """
        Requires the full list of questions and examples.
        """
        self.question_bank = question_bank # Assumes a list of question dicts
        self.example_bank = example_bank   # Assumes a dict of example dicts (lessons)
        print(f"  [Policy] Initialized with {len(question_bank)} questions.")

    def _select_question(self, student_history, current_concept_id):
        """
        Finds the hardest available question for the current concept.
        """
        # 1. Filter questions by concept
        questions_for_concept = [
            q for q in self.question_bank
            if q.get('concept_id') == current_concept_id
        ]
        if not questions_for_concept:
            return None # No questions found for this concept

        # 2. Filter out seen questions
        seen_question_ids = set(
            interaction['question_id'] for interaction in student_history
        )
        available_questions = [
            q for q in questions_for_concept
            if q.get('id') not in seen_question_ids
        ]

        # 3. Select the hardest available one
        if not available_questions:
            print(f"  [Policy] No unseen questions found for concept {current_concept_id}.")
            return None
        else:
            # Find question with max difficulty
            return max(available_questions, key=lambda q: q.get('difficulty', 0))

    def _select_example(self, current_concept_id):
        """
        Finds a random example (lesson) for the concept.
        """
        # Assumes example_bank is a dict like {"l1": {"concept_id": "c1", ...}}
        examples_for_concept = [
            ex for ex in self.example_bank.values()
            if ex.get('concept_id') == current_concept_id
        ]
        if examples_for_concept:
            return random.choice(examples_for_concept)
        else:
            print(f"  [Policy] No examples found for concept {current_concept_id}.")
            return None

    def select_action(self, student_state, student_history, current_concept_id):
        """
        The main method called by the Tutor.
        Decides the next action based on a priority list.
        """
        # --- Priority 1: Try to select a question ---
        question = self._select_question(student_history, current_concept_id)
        if question is not None:
            return ("question", question)

        # --- Priority 2: Try to select an example ---
        print(f"  [Policy] No questions left for {current_concept_id}. Trying example.")
        example = self._select_example(current_concept_id)
        if example is not None:
            return ("example", example)

        # --- Priority 3: Give up ---
        print(f"  [Policy] No questions or examples left for {current_concept_id}.")
        return ("end_concept", {"concept_id": current_concept_id, "message": "Concept complete!"})
