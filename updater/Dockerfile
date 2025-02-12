# Use the latest stable Python version
FROM python:3.12
ENV PYTHONUNBUFFERED True

# Add a non-root user with UID 10013
RUN groupadd -g 10013 appgroup && \
    useradd -u 10013 -g appgroup -m appuser

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Set working directory
WORKDIR $APP_HOME

# Copy dependency file first for efficient caching
COPY requirements.txt .

# Copy the entire application
COPY . $APP_HOME

# Set appropriate permissions
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER 10013

# Default command to run your script (modify if needed)
CMD ["python", "script.py"]
