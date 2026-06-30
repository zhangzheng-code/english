# ============================================================
# FastAPI AI Service - Production Dockerfile
# ============================================================
# 构建: docker build -t server-ai .
# 运行: docker run -p 3001:3001 --env-file .env server-ai
# ============================================================

FROM python:3.12-slim AS base

# 系统依赖：psycopg 编译需要 gcc + libpq-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- 依赖安装（利用 Docker 层缓存）----
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ---- 应用代码 ----
COPY . .

# ---- 运行 ----
EXPOSE 3001

# 健康检查：每 30s 探测 /ai/v1/，连续 3 次失败则标记 unhealthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3001/ai/v1/ || exit 1

# Linux 环境直接用 uvicorn，PostgresSaver 将自动激活
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "3001", "--workers", "1"]
