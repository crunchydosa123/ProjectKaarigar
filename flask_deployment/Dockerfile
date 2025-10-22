FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install build dependencies for PyAudio
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
