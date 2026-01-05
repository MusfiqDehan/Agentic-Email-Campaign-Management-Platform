# Use the official Python image from Docker Hub
FROM python:3.12-slim

# Set environment variables to avoid buffering and to set the working directory inside the container
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt /usr/src/app/

# Install curl + build deps, then uv
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential \
 && curl -LsSf https://astral.sh/uv/install.sh | sh \
 && export PATH="/root/.local/bin:$PATH" \
 && uv pip install --system --no-cache -r requirements.txt \
 && apt-get purge -y curl build-essential \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Copy the entire Django project into the container
COPY . /usr/src/app/

# Create migrations 
ENTRYPOINT ["bash", "docker_entrypoint.sh"]

# Expose the application port
EXPOSE 8001

# Command to run the Django development server
CMD ["daphne", "-p", "8001", "-b", "0.0.0.0", "config.asgi:application"]