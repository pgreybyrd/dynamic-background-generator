import json

def load_state(state_path):
    if not state_path.exists():
        return {}

    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_state(state, state_path):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)