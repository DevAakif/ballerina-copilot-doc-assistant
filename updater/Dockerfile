# Use the latest stable Python version
FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app/updater  # Working directory inside updater

# Create a non-root user for security
RUN groupadd -g 10013 appgroup && \
    useradd -u 10013 -g appgroup -m appuser

# Set working directory
WORKDIR $APP_HOME

# Copy only the updater folder (including requirements.txt)
COPY . .

# Install dependencies using requirements.txt from updater
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set appropriate permissions
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER 10013

# Default command to run your script
CMD ["python", "main.py"]
