DB_FILE = "responses.db"
MODEL_FILE = "models.json"

with open(MODEL_FILE, 'r') as f:
    from json import load
    MODEL_POOL = load(f)
