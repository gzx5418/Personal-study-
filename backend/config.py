import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LLM_BINDING: str = os.getenv("LLM_BINDING", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_HOST: str = os.getenv("LLM_HOST", "https://api.openai.com/v1")

    EMBEDDING_BINDING: str = os.getenv("EMBEDDING_BINDING", "openai")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_HOST: str = os.getenv("EMBEDDING_HOST", "https://api.openai.com/v1/embeddings")

    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./data/chroma")
    KNOWLEDGE_DIR: str = os.getenv("KNOWLEDGE_DIR", "./data/knowledge_bases")
    MASTERY_FILE: str = os.getenv("MASTERY_FILE", "./data/mastery.json")
    PROFILE_FILE: str = os.getenv("PROFILE_FILE", "./data/profile.json")
    SESSION_DB: str = os.getenv("SESSION_DB", "./data/sessions.db")

    COURSE_ID: str = os.getenv("COURSE_ID", "python_programming")

    MAX_HISTORY_TURNS: int = 20
    SUMMARY_TOKEN_RATIO: float = 0.4
    HISTORY_TOKEN_RATIO: float = 0.35

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))


settings = Settings()
