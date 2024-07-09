# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Set proxy environment variables (replace with your proxy details)
# ENV http_proxy http://192.168.254.1:3128

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Command to run your application
CMD ["python", "ScrumAssistance-full.py"]
