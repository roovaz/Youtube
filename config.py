import os

class Config:
    """Configuration from environment variables"""

    # API Configuration
    RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
    RAPIDAPI_HOST = 'twitter241.p.rapidapi.com'
    RAPIDAPI_BASE_URL = 'https://twitter241.p.rapidapi.com'

    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database Configuration
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'twitter_scraper.db')

    # Scraping Configuration
    DEFAULT_MAX_TWEETS = 100
    DEFAULT_MAX_COMMENTS = 50
    DEFAULT_MAX_AGE_DAYS = 30
    API_DELAY = 0.5  # Delay between API calls in seconds
    REQUEST_TIMEOUT = 30  # Request timeout in seconds

    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.RAPIDAPI_KEY:
            raise ValueError("RAPIDAPI_KEY environment variable is required")
