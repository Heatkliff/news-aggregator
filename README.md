# News Aggregator

A comprehensive news aggregation system that collects articles from various sources using both RSS feeds and custom web scraping. The system stores all news in a PostgreSQL database and provides flexible search functionality.

## Features

- Collection of news articles from multiple sources
- Support for RSS feeds
- Custom web scraping capabilities
- Flexible and powerful search functionality
- Asynchronous task processing with Celery
- Dockerized deployment

## Tech Stack

- **Backend**: Django
- **Database**: PostgreSQL
- **Caching**: Redis
- **Task Queue**: Celery
- **Containerization**: Docker

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Django settings
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
DB_NAME=news_aggregator
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=postgres
DB_PORT=5432

# Redis settings
REDIS_HOST=redis
REDIS_PORT=6379

# Celery settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Running with Docker

1. Build the Docker images:
```
docker-compose build
```

2. Start the services:
```
docker-compose up
```

3. Run migrations:
```
docker-compose exec web python manage.py migrate
```

4. Create a superuser:
```
docker-compose exec web python manage.py createsuperuser
```

## Development

### Manual Setup (without Docker)

1. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables (see above)

4. Run migrations:
```
python manage.py migrate
```

5. Start the development server:
```
python manage.py runserver
```

### Testing

Run tests with:
```
python manage.py test
```