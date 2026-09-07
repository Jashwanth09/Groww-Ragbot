import sys, json, os

# Add required paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, 'phase2'))
sys.path.append(os.path.join(SCRIPT_DIR, 'phase3'))
sys.path.append(os.path.join(SCRIPT_DIR, 'phase4'))
sys.path.append(os.path.join(SCRIPT_DIR, 'scripts'))

from dotenv import load_dotenv
load_dotenv()

from answer_generator import AnswerGenerator

if __name__ == "__main__":
    gen = AnswerGenerator()
    result = gen.generate_answer('what is the nav of ICICI large cap fund direct growth?')
    with open('rag_output.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
