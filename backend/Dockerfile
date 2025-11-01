FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

# Install build dependencies for PyAudio + FFmpeg
RUN apt-get update && apt-get install -y

RUN pip install --upgrade pip
RUN pip install --default-timeout=100 --prefer-binary -r requirements.txt

COPY . .

CMD ["python", "app.py"]