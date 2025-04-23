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
SP_USER_LOGIN=superuser_login
SP_USER_PASS=superuser_password

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

Build the Docker images and start the services:
```
docker compose up --build
```

### Load predefined sources

To automatically populate the database with a predefined list of news sources, use the management command below:

```bash
docker-compose exec web python manage.py load_sources
```


## RSS Parsing

The system supports collecting news from RSS feeds of various sources. Each active source in the database that has a valid `rss_url` can be automatically parsed using the built-in management command.

### Run RSS parsing for all sources

To fetch and parse RSS articles from all active sources stored in the database, run the following command in Docker:

```
docker-compose exec web python manage.py rss_parse
```

This command will:
- Load all active `Source` objects with non-empty `rss_url`
- Use a site-specific configuration if defined (or fall back to a default config)
- Extract content, tags, and categories
- Store the parsed articles in the database or output them to a JSON file during development

### Customizing RSS Extraction Per Site

The RSS parser uses a configuration dictionary to control how content, tags, and categories are extracted for each site. You can define custom logic for any domain by updating the `SITE_CONFIGS` dictionary.

Example configuration for a hypothetical site `example.com`:

```python
"example.com": {
    "name": "Example News",
    "domain_patterns": ["example.com"],
    "content_extractors": [
        lambda entry: entry.get('fulltext', ''),
        lambda entry: entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
        lambda entry: entry.get('summary', ''),
        lambda entry: entry.get('description', '')
    ],
    "tag_extractors": [
        lambda entry: [tag.term.strip() for tag in entry.get('tags', []) if hasattr(tag, 'term') and tag.term.strip()],
        lambda entry: [entry.get('category', '').strip()] if isinstance(entry.get('category'), str) else [],
        lambda entry: [cat.strip() for cat in entry.get('category', []) if cat and cat.strip()] if isinstance(entry.get('category'), list) else []
    ],
    "category_extractors": [
        lambda entry: entry.get('category', '').strip() if isinstance(entry.get('category'), str) else '',
        lambda entry: entry.get('category', [''])[0].strip() if isinstance(entry.get('category'), list) and entry.get('category') else ''
    ],
    "content_cleaners": []
}
```

If no match is found for a given source domain or name, the default configuration will be used instead:

```python
"default": {
    "name": "Default",
    "domain_patterns": [],
    "content_extractors": [...],
    "tag_extractors": [...],
    "category_extractors": [...],
    "content_cleaners": []
}
```

This setup allows easy per-source customization of parsing behavior without hardcoding logic.



### Database Population Commands

Use these commands to populate your database with test data:

Basic command - creates 50 random news articles without clearing existing data:
```
docker-compose exec web python manage.py populate_db
```

Creates a specific number of news articles (100 in this example):
```
docker-compose exec web python manage.py populate_db --news_count=100
```

Clears all existing data before populating with 50 default news articles:
```
docker-compose exec web python manage.py populate_db --clear
```

Clears all existing data and creates 100 news articles:
```
docker-compose exec web python manage.py populate_db --clear --news_count=100
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