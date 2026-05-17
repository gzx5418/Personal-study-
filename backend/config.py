import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "智学助手")
    DEFAULT_USER_ID: str = os.getenv("DEFAULT_USER_ID", "demo_student")
    LLM_BINDING: str = os.getenv("LLM_BINDING", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_REASONING_MODEL: str = os.getenv("LLM_REASONING_MODEL", "deepseek-ai/DeepSeek-V3.2")
    LLM_VISION_MODEL: str = os.getenv("LLM_VISION_MODEL", "zai-org/GLM-4.6V")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_HOST: str = os.getenv("LLM_HOST", "https://api.openai.com/v1")

    EMBEDDING_BINDING: str = os.getenv("EMBEDDING_BINDING", "openai")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_HOST: str = os.getenv("EMBEDDING_HOST", "https://api.openai.com/v1/embeddings")

    CHROMA_DIR: str = os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(__file__), "data", "chroma"))
    KNOWLEDGE_DIR: str = os.getenv("KNOWLEDGE_DIR", os.path.join(os.path.dirname(__file__), "data", "knowledge_bases"))
    MASTERY_FILE: str = os.getenv("MASTERY_FILE", os.path.join(os.path.dirname(__file__), "data", "mastery.json"))
    PROFILE_FILE: str = os.getenv("PROFILE_FILE", os.path.join(os.path.dirname(__file__), "data", "profile.json"))
    SESSION_DB: str = os.getenv("SESSION_DB", os.path.join(os.path.dirname(__file__), "data", "sessions.db"))

    COURSE_ID: str = os.getenv("COURSE_ID", "python_programming")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "*")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    RAG_MIN_SCORE: float = float(os.getenv("RAG_MIN_SCORE", "2"))
    PPT_MASTER_SCRIPTS_DIR: str = os.getenv(
        "PPT_MASTER_SCRIPTS_DIR",
        os.path.join(os.path.dirname(__file__), "scripts"),
    )

    MAX_HISTORY_TURNS: int = 20
    SUMMARY_TOKEN_RATIO: float = 0.4
    HISTORY_TOKEN_RATIO: float = 0.35

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))


settings = Settings()
