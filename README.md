
# Daily Report Bot

A Telegram bot designed to help teams submit and manage daily reports. The bot uses SQLite for storage and supports Docker for containerized deployment.

**[View this document in Persian (نسخه فارسی)](README_FA.md)**

---

## Features

1. **Daily Reports**:
   - Users can submit daily reports containing:
     - Tasks worked on today.
     - Questions or blockers encountered.
     - Tasks planned for tomorrow.

2. **Automated Reminders**:
   - Sends reminders to users to submit their reports.
   - Notifies the group about pending reports.

3. **Report Summaries**:
   - Sends daily consolidated reports to a group.

4. **Containerized Deployment**:
   - The bot is containerized using Docker for easy deployment.

---

## Setup

### Prerequisites

- **Environment**:
  - Python 3.7+
  - Docker and Docker Compose
- **Environment Variables** (to be defined in a `.env` file):
  - `TOKEN`: Telegram bot token
  - `GROUP_ID`: Target group ID
  - `REPORT_TOPIC_ID`: Topic ID for report notifications
  - `ALERT_TOPIC_ID`: Topic ID for report reminders
  - `HTTP_PROXY` (optional): Proxy URL for connecting to Telegram servers

---

## Docker Configuration

### Dockerfile

The `Dockerfile` builds a lightweight container for the bot:

```dockerfile
# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Set proxy environment variables (replace with your proxy details)
ENV http_proxy=${HTTP_PROXY}

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY ./ScrumAssistance-full.py .

# Command to run your application
CMD ["python", "ScrumAssistance-full.py"]
```

---

### Docker Compose

The `docker-compose.yml` file configures the bot container and ensures data persistence:

```yaml
version: "3.1"

services:
  dailyreporter:
    container_name: dailyreporter
    build: .
    logging:
      options:
        max-size: "500m"
        max-file: "5"
    volumes:
      - daily-reporter-data:/app/data
    env_file: .env
    networks:
      - telegram-network

networks:
  telegram-network:
    driver: bridge

volumes:
  daily-reporter-data:
    driver: local
    driver_opts:
      o: bind
      type: none
      device: "./dailyreporter"
```

---

## Deployment

### Running Locally

1. Clone the repository or copy the bot script.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python ScrumAssistance-full.py
   ```

### Running with Docker

1. Build the Docker image:
   ```bash
   docker-compose build
   ```
2. Start the bot:
   ```bash
   docker-compose up
   ```
3. Stop the bot:
   ```bash
   docker-compose down
   ```

---

## Scheduled Jobs

The bot automatically sends reminders and reports:
- **16:00**: Requests daily tasks from users.
- **18:00**: Reminds users who haven't submitted reports.
- **09:00 (Next Day)**: Sends consolidated reports to the group.

---

## Commands

- `/report`: Start the daily report submission process.
- `/cancel`: Cancel the report submission process.
- `/getreports`: Fetch and send reports to the group manually.

---

## Database Schema

The bot uses SQLite with the following schema:

- **Table**: `reports`
  - `id`: Primary Key (Integer)
  - `user_id`: Telegram User ID (Integer)
  - `tasks_today`: Tasks worked on today (String)
  - `blockers`: Questions or blockers (String)
  - `tasks_tomorrow`: Tasks planned for tomorrow (String)
  - `timestamp`: Report submission timestamp (DateTime)

---

## Extensibility

1. **Custom Database**:
   Replace SQLite with other databases by modifying the SQLAlchemy engine configuration.

2. **Custom Reminders**:
   Add or change scheduled jobs to meet specific requirements.

3. **User Management**:
   Enhance the bot to manage group members and track user activity.

---

---

### Persian Version (نسخه فارسی)

**[View this document in English](README_FA.md)**

---

