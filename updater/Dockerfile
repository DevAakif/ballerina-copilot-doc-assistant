# Use the latest stable Python version
FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN groupadd -g 10013 appgroup && \
    useradd -u 10013 -g appgroup -m appuser

# Set working directory inside updater folder
WORKDIR /app

# Copy the entire updater folder, including requirements.txt
COPY . .

# Install dependencies using requirements.txt from the updater folder
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set appropriate permissions
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER 10013

# Default command to run your entry script (main.py)
CMD ["python", "main.py"]
