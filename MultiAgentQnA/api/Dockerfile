FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose the port the service runs on
EXPOSE 5001

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]

