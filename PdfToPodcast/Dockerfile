FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy the rest of the application files into the container
COPY simple_backend.py .

# Expose the port the service runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "simple_backend:app", "--host", "0.0.0.0", "--port", "8000"]