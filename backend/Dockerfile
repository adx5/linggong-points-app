# backend/Dockerfile (CloudBase 云托管适配版)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 🚨 修复硬伤 1：EXPOSE 不支持变量展开，必须写死，具体端口由 CMD 中的 $PORT 决定
EXPOSE 8888

CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8888}"]