FROM python:3.11-slim

WORKDIR /app

# Copy only what we need first for caching dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Set environment variables for security; override when running
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Default command, Render will use $PORT
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "3"]
