# !/usr/bin/env python
"""
Initialize the news parser directory structure.
Run this script once to set up the necessary directories.
"""
import os


def create_directory(path):
    """Create a directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")


def main():
    """Initialize the news parser directory structure"""
    # Get the base directory (where this script is located)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create directories
    create_directory(os.path.join(base_dir, 'news_parser'))
    create_directory(os.path.join(base_dir, 'news_parser', 'spiders'))
    create_directory(os.path.join(base_dir, 'output'))

    print("News parser directory structure initialized.")


if __name__ == "__main__":
    main()