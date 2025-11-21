FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

# --- THE FIX IS HERE: Added --timeout 600 ---
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "600", "app:app"]