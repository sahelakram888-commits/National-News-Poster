FROM python:3.11-slim

WORKDIR /app

# Install system deps for fonts and Pillow
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure output dir
RUN mkdir -p output assets/fonts

# Run once on start, then scheduler if needed
CMD ["python", "src/main.py", "--schedule"]
