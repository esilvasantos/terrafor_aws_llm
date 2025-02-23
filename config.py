class Config:
    DB_PARAMS = {
        "dbname": "",
        "user": "",
        "password": "",
        "host": "localhost",
        "port": "5432"
    }

    OLLAMA_CONFIG = {
        "BASE_URL": "http://localhost:11434/api/generate",
        "MODEL": "llama3.2",
        "OPTIONS": {
            "temperature": 0.3,
            "num_predict": 100,
            "timeout": 300
        }
    }
