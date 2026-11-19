FROM python:3.11-slim

WORKDIR /app

# 先拷贝依赖文件并安装，利用 Docker 缓存机制加速后续构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝后端所有代码
COPY . .

# 对外暴露 8000 端口
EXPOSE 8000

# 注意：启动命令在 docker-compose.yml 中已指定（包含 alembic upgrade head）