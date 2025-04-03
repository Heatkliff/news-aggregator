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