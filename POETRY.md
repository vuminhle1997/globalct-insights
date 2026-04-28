# Poetry Setup & Docker Deployment

## Local Development Setup with Poetry

### Prerequisites
- Python 3.8 or higher
- Poetry installed ([install guide](https://python-poetry.org/docs/#installation))

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llama-rag
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

4. **Verify installation**
   ```bash
   poetry show
   ```

### Running Locally

```bash
# Run the application
poetry run python main.py

# Or run specific commands
poetry run python -m your_module
```

### Adding New Dependencies

```bash
# Add a new package
poetry add package-name

# Add a dev dependency
poetry add --group dev package-name
```

### Update Dependencies

```bash
poetry update
```

---

## Docker Setup for Backend Production

### Prerequisites
- Docker installed
- Docker Compose (optional, for multi-container setups)

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no virtual env in container)
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY . .

# Expose port (adjust as needed)
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "python", "main.py"]
```

### Building the Docker Image

```bash
docker build -t llama-rag:latest .
```

### Running the Container

```bash
# Basic run
docker run -p 8000:8000 llama-rag:latest

# With environment variables
docker run -p 8000:8000 \
  -e ENV_VAR=value \
  llama-rag:latest

# With volume mount for logs
docker run -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  llama-rag:latest
```

### Docker Compose (Optional)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: llama-rag-backend
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

Run with Docker Compose:

```bash
docker-compose up -d
```

### Production Best Practices

- Use a `.dockerignore` file to exclude unnecessary files
- Keep images small by using minimal base images (python:3.11-slim)
- Don't run as root; create a non-root user
- Use environment variables for configuration
- Enable container health checks
- Implement proper logging

### Health Check Example

Add to Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD poetry run python -c "import requests; requests.get('http://localhost:8000/health')"
```
