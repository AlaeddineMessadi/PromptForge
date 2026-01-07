FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py index.html ./
COPY assets ./assets
COPY images ./images
COPY *.json ./

ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
