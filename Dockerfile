# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /gateproadmin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    gcc \
    postgresql-client \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn
    

# Copy the current directory contents into the container at /app
COPY . /rempro/

# Run collectstatic
RUN python manage.py collectstatic --no-input
# Expose port 8000 to the outside world
EXPOSE 8001

# Run the Django app
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "rempro.wsgi:application"]
