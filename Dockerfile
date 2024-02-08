# Use an official Python runtime as the parent image
FROM python:3.10

# Set the working directory in the container to /app
WORKDIR /app

# Install Poppler for pdf2image
RUN apt-get update && \
    apt-get install -y poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["streamlit", "run", "main.py"]
