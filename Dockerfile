FROM python:3.12
ENV PYTHONUNBUFFERED True

# Add a non-root user with UID 10013
RUN groupadd -g 10013 appgroup && \
    useradd -u 10013 -g appgroup -m appuser

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . $APP_HOME

# Set permissions for the non-root user
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER 10013

# Expose port and set the default command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
