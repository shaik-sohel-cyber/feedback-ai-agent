# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app will run on
EXPOSE 10000

# Define the command to run your app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
