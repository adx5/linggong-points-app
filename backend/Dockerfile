# backend/Dockerfile (CloudBase 云托管适配版，写死 80 端口)
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露 80 端口
EXPOSE 80

# 🚨 修复健康检查探针失败：直接绑定 0.0.0.0:80，不依赖环境变量
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:80"]