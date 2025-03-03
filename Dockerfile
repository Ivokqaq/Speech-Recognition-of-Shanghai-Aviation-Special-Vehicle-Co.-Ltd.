# 使用官方 Python 镜像作为基础
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD gunicorn --bind 0.0.0.0:$PORT app:app