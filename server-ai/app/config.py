from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://deploy:password@localhost:5432/english"
    langchain_database_url: str = "postgresql://deploy:password@localhost:5433/langchain"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_api_model: str = "deepseek-chat"
    deepseek_reasoner_api_model: str = "deepseek-reasoner"

    # Bocha Search
    bocha_search_url: str = "https://api.bochaai.com/v1/web-search"
    bocha_api_key: str = ""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Email
    email_host: str = ""
    email_port: int = 465
    email_use_ssl: bool = True
    email_user: str = ""
    email_password: str = ""
    email_from: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
