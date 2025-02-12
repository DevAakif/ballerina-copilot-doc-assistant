# Use the latest stable Python version
FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Create a non-root user for security
RUN groupadd -g 10013 appgroup && \
    useradd -u 10013 -g appgroup -m appuser

# Set working directory
WORKDIR $APP_HOME

# Copy dependency file first for efficient caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . $APP_HOME

# Set appropriate permissions
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER 10013

# Default command to run your script
CMD ["python", "main.py"]
