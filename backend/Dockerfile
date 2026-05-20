# We use a lightweight Python 3.11 image as the base.
FROM python:3.11-slim

# Set the working directory for the application.
WORKDIR /app

# Prevent Python from writing .pyc files to disk and ensure logs are output immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building Python packages.
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source code into the container.
COPY . .

# Expose port 8080 to match Google Cloud Run default expectations.
EXPOSE 8080

# Run database setup (creates tables and admin user) then start the FastAPI application.
# We use '|| true' so that if the database is misconfigured, it doesn't crash the entire deployment.
CMD sh -c "python setup_admin.py || echo 'Database setup failed, but starting server anyway...'; uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"
