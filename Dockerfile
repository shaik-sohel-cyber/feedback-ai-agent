# Use a complete base image that has many common system libraries
FROM python:3.11-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# 1. Install system dependencies required by Google Chrome
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    gnupg \
    --no-install-recommends

# 2. Add Google's official repository and install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends

# 3. Install the correct ChromeDriver version to match the installed Chrome
RUN CHROME_VERSION=$(google-chrome --version | cut -f 3 -d ' ' | cut -d '.' -f 1-3) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | python3 -c "import json, sys; data=json.load(sys.stdin); print(next(v['version'] for v in reversed(data['versions']) if v['version'].startswith('$CHROME_VERSION')))") \
    && wget -q --continue -P /tmp "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver-linux64.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver-linux64.zip \
    && chmod +x /usr/local/bin/chromedriver-linux64/chromedriver

# Add the chromedriver to the system's PATH
ENV PATH="/usr/local/bin/chromedriver-linux64:${PATH}"

# 4. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application's code into the container
COPY . .

# Expose the port your app will run on
EXPOSE 10000
# Define the command to start your application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

