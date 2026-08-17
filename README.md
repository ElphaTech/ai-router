# How to use

Download the repo:
```sh
git clone https://github.com/ElphaTech/ai-router.git
cd ai-router
```

Make virtual environment and install requirements:
```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You need a `models.json` file similar to the following. You can have as many models as you want, the lowest priority value will be picked first.
```json
[
    {
        "name": "openrouter_free",
        "priority": 2,
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "sk-or-v1-token",
        "target_model": "openrouter/free",
        "provider": "openrouter",
        "supports_thinking": true
    }
]
```

Run it:
```sh
python main.py
```

Point your project to it (example using openai library):
```py
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)
```
