FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .


# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose the port the service runs on
EXPOSE 8002

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
