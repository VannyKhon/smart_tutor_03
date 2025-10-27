import json
import os

class ContentManager:
    """
    Loads and manages all content (concepts, questions, lessons)
    from JSON files.
    """
    def __init__(self, concepts_file, questions_file, lessons_file):
        """
        Loads the data from the specified file paths.
        """
        print(f"  [ContentManager] Loading concepts from {concepts_file}")
        self.concepts = self._load_json(concepts_file)
        
        print(f"  [ContentManager] Loading questions from {questions_file}")
        self.questions = self._load_json(questions_file)
        
        print(f"  [ContentManager] Loading lessons from {lessons_file}")
        self.lessons = self._load_json(lessons_file)

    def _load_json(self, file_path):
        """Helper function to load a JSON file."""
        # In a real app, you'd add error handling if files are missing
        # For now, we assume they exist when app.py calls this.
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"  [ContentManager] WARNING: Data file not found: {file_path}. Returning empty data.")
            return {} # Return empty dict/list if file not found
        except json.JSONDecodeError:
            print(f"  [ContentManager] WARNING: Error decoding JSON from file: {file_path}. Returning empty data.")
            return {}

    def get_question(self, question_id):
        """Gets a single question by its ID."""
        # Assumes self.questions is a list of dictionaries
        for q in self.questions:
            if q.get('id') == question_id:
                return q
        print(f"  [ContentManager] Warning: Question ID '{question_id}' not found.")
        return None

    def get_lesson(self, lesson_id):
        """Gets a single lesson by its ID."""
        # Assumes self.lessons is a dictionary where keys are lesson_ids
        return self.lessons.get(lesson_id, None)

    # You might need a get_concept method later too
    # def get_concept(self, concept_id):
    #     """Gets a single concept by its ID."""
    #     concepts_list = self.concepts.get('concepts', [])
    #     for c in concepts_list:
    #         if c.get('id') == concept_id:
    #             return c
    #     return None
