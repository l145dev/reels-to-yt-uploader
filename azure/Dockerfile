FROM python:3.11-slim

# Install system dependencies (ffmpeg is required for moviepy/whisper)
RUN apt-get update && apt-get install -y \
    cron \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary files
COPY upload_vids.py .
COPY client_secrets.json .
COPY token.json .

# Create necessary directories
RUN mkdir videos
RUN touch schedule_state.json

# Setup Cron for 11 PM
# We use the timezone mount trick so 23:00 means 23:00 Belgium time
RUN echo "0 23 * * * root /usr/local/bin/python /app/upload_vids.py >> /var/log/cron.log 2>&1" > /etc/cron.d/scheduler

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/scheduler

# Apply cron job
RUN crontab /etc/cron.d/scheduler

# Create log file
RUN touch /var/log/cron.log

# Run cron in foreground
CMD ["cron", "-f"]