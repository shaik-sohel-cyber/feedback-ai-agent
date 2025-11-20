# Use 'bookworm' (Debian 12) instead of 'buster' (Debian 10)
FROM python:3.10-slim-bookworm

# Install Chrome and dependencies
# In Bookworm, we can install chromium and the driver directly
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables so Selenium knows where to look
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 5000

# Run the app using Gunicorn (Production server)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]