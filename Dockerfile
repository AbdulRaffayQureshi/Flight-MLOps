# Use a lightweight, official Python 3.11 image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and force stdout logging (good for Docker)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set our working directory inside the container
WORKDIR /workspace

# Install system-level build tools required by some ML libraries (like XGBoost)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy our dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our project files into the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]