import os
from flask import Flask, render_template, request, jsonify

# --- Imports from your src ---
# Ensure these files exist in the src folder with the correct classes
from src.content import ContentManager
from src.student import Student
from src.tracers import TransformerKnowledgeTracer # Using placeholder for now
from src.policies import SimpleDifficultyPolicy
from src.tutor import Tutor

# --- Create and configure the Flask App ---
app = Flask(__name__)
# The template folder is expected to be named "templates" by default
print("Flask app created.")

# --- Define Data File Paths ---
# Use os.path.join for cross-platform compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'model')

CONCEPTS_FILE = os.path.join(DATA_DIR, 'knowledge.json')
QUESTIONS_FILE = os.path.join(DATA_DIR, 'question.json')
LESSONS_FILE = os.path.join(DATA_DIR, 'lesson.json')
MODEL_FILE_PATH = os.path.join(MODEL_DIR, 'model.pt') # Placeholder path

LATENT_DIM_D = 32 # Example dimension for student state

# --- Global variable to hold the tutor instance ---
# We use None initially and initialize in a try block
tutor_instance = None

# --- Initialize All Components ---
try:
    print("--- Initializing Tutor System ---")
    
    # Create necessary directories if they don't exist (useful locally)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Create dummy data files if they don't exist (for initial run)
    if not os.path.exists(CONCEPTS_FILE):
        with open(CONCEPTS_FILE, 'w') as f: f.write('{"concepts": [], "prerequisites": []}')
        print(f"Created dummy {CONCEPTS_FILE}")
    if not os.path.exists(QUESTIONS_FILE):
         with open(QUESTIONS_FILE, 'w') as f: f.write('[]')
         print(f"Created dummy {QUESTIONS_FILE}")
    if not os.path.exists(LESSONS_FILE):
         with open(LESSONS_FILE, 'w') as f: f.write('{}')
         print(f"Created dummy {LESSONS_FILE}")
         
    # Create dummy model file if it doesn't exist
    if not os.path.exists(MODEL_FILE_PATH):
        with open(MODEL_FILE_PATH, 'w') as f: f.write('dummy model data')
        print(f"Created dummy {MODEL_FILE_PATH}")


    print("Initializing ContentManager...")
    content_manager = ContentManager(
        concepts_file=CONCEPTS_FILE,
        questions_file=QUESTIONS_FILE,
        lessons_file=LESSONS_FILE
    )
    print("ContentManager initialized.")

    # Need actual content for policy to work, get from manager
    # Handle potential empty files from dummy creation
    questions_bank = content_manager.questions if isinstance(content_manager.questions, list) else []
    examples_bank = content_manager.lessons if isinstance(content_manager.lessons, dict) else {}
    all_concepts_data = content_manager.concepts if isinstance(content_manager.concepts, dict) else {}

    print(f"Loaded {len(questions_bank)} questions, {len(examples_bank)} examples, and {len(all_concepts_data.get('concepts', []))} concepts.")

    print("Initializing Student...")
    # Using a fixed student ID for this simple web version
    student = Student(student_id="web_user_01", latent_dim_d=LATENT_DIM_D)
    print("Student initialized.")

    print("Initializing Tracer...")
    # Inject content_manager for the real tracer later
    tracer = TransformerKnowledgeTracer(
        model_path=MODEL_FILE_PATH,
        content_manager=content_manager # Needed even for placeholder if it accesses content
    )
    print("Tracer initialized.")

    print("Initializing Policy...")
    policy = SimpleDifficultyPolicy(
        question_bank=questions_bank,
        example_bank=examples_bank
    )
    print("Policy initialized.")

    print("Initializing Tutor...")
    # Create the single tutor instance
    tutor_instance = Tutor(student, policy, tracer, content_manager)
    print("All tutor components initialized successfully.")
    print("--- Initialization Complete ---")

except Exception as e:
    print(f"--- FATAL ERROR DURING INITIALIZATION ---")
    print(f"Failed to initialize components: {e}")
    # Set tutor_instance to None so web routes know initialization failed
    tutor_instance = None
    # Re-raise the exception to stop the app if needed, or handle differently
    # raise e

# --- Flask Web Routes ---
@app.route('/')
def index():
    # Render the HTML template
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_session():
    if tutor_instance is None:
        return jsonify({"error": "Tutor failed to initialize"}), 500
    try:
        action_type, content, current_concept_id = tutor_instance.start_session()
        # Send the first action and the full list of concepts
        return jsonify({
            "action": {"type": action_type, "content": content},
            "concepts": tutor_instance.concepts_to_teach, # Send sorted list
            "current_concept_id": current_concept_id
        })
    except Exception as e:
        print(f"Error in /start route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/answer', methods=['POST'])
def handle_answer():
    if tutor_instance is None:
        return jsonify({"error": "Tutor failed to initialize"}), 500
    try:
        data = request.json
        question_id = data.get('question_id')
        user_answer = data.get('user_answer')
        response_time_ms = data.get('response_time_ms')

        if question_id is None or user_answer is None or response_time_ms is None:
             return jsonify({"error": "Missing 'question_id', 'user_answer', or 'response_time_ms'"}), 400

        action_type, content, current_concept_id = tutor_instance.submit_answer(
            question_id,
            user_answer,
            response_time_ms
        )
        # Send the next action and the current concept ID
        return jsonify({
            "action": {"type": action_type, "content": content},
            "current_concept_id": current_concept_id
        })
    except Exception as e:
        print(f"Error in /answer route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/next_concept', methods=['POST'])
def next_concept():
    if tutor_instance is None:
        return jsonify({"error": "Tutor failed to initialize"}), 500
    try:
        # Manually advance tutor's concept index
        tutor_instance.current_concept_index += 1
        print(f"[App] Frontend requested next concept. Moving to index {tutor_instance.current_concept_index}.")
        
        # Get the first action for the *new* concept
        action_type, content, current_concept_id = tutor_instance._get_next_action()
        
        return jsonify({
            "action": {"type": action_type, "content": content},
            "current_concept_id": current_concept_id
        })
    except Exception as e:
        print(f"Error in /next_concept route: {e}")
        return jsonify({"error": str(e)}), 500

# --- Run the App ---
if __name__ == "__main__":
    print("Starting Flask server...")
    # Use host='0.0.0.0' to make it accessible on your network
    # Use debug=True for development (auto-reloads on code changes)
    # Use use_reloader=True to enable the reloader
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False) 
    # Note: Set use_reloader=False if debug=True causes issues on some systems
