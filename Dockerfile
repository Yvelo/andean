# Stage 1: Install dependencies
FROM python:3.9-slim AS build

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Copy necessary files and dependencies for running the application
FROM python:3.9-slim

WORKDIR /app

# Copy the necessary application files
COPY . /app

# Copy the api-keys.json from Google Cloud Built temp environment
COPY  api-keys.json api-keys.json
COPY  google-api-credentials.json google-api-credentials.json

# Copy the installed Python packages from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

RUN pip install gunicorn

EXPOSE 8080

#ENTRYPOINT ["python", "run.py"]
CMD ["gunicorn", "-b", ":8080", "app.controller.controller:app"]
