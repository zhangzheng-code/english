from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://deploy:password@localhost:5432/english"
    langchain_database_url: str = "postgresql://deploy:password@localhost:5433/langchain"

    # DeepSeek / DashScope (Aliyun)
    deepseek_api_key: str = ""
    deepseek_api_model: str = "deepseek-chat"
    deepseek_reasoner_api_model: str = "deepseek-reasoner"
    dashscope_api_key: str = ""
    asr_model: str = "sensevoice-v1"

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

    # JWT（与原 NestJS SECRET_KEY 保持一致）
    secret_key: str = "shjdbswd6879021312gsdfjsd"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Alipay
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""
    alipay_gateway: str = "https://openapi.alipay.com/gateway.do"
    alipay_notify_url: str = ""

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "english"
    minio_secure: bool = False
    temp_upload_dir: str = "/tmp/chunks"
    chroma_db_dir: str = "./chroma_db"

    # ClickHouse
    clickhouse_url: str = "http://localhost:8123"
    clickhouse_username: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
