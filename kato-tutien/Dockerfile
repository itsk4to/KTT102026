FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY kato-tutien/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY kato-tutien/ /app/
CMD ["python", "bot.py"]
