import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from config import Config


class Database:
    """SQLite database manager for Twitter scraper"""

    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    description TEXT,
                    location TEXT,
                    profile_image_url TEXT,
                    profile_banner_url TEXT,
                    followers_count INTEGER,
                    following_count INTEGER,
                    tweets_count INTEGER,
                    likes_count INTEGER,
                    is_verified INTEGER,
                    is_blue_verified INTEGER,
                    account_created_at TEXT,
                    scraped_at TEXT NOT NULL,
                    raw_json TEXT
                )
            ''')

            # Tweets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tweets (
                    tweet_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    full_text TEXT,
                    created_at TEXT,
                    retweet_count INTEGER,
                    favorite_count INTEGER,
                    reply_count INTEGER,
                    quote_count INTEGER,
                    views_count INTEGER,
                    language TEXT,
                    has_media INTEGER,
                    media_urls TEXT,
                    hashtags TEXT,
                    scraped_at TEXT NOT NULL,
                    raw_json TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Comments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    parent_tweet_id TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    display_name TEXT,
                    full_text TEXT,
                    created_at TEXT,
                    favorite_count INTEGER,
                    reply_count INTEGER,
                    scraped_at TEXT NOT NULL,
                    raw_json TEXT,
                    FOREIGN KEY (parent_tweet_id) REFERENCES tweets(tweet_id)
                )
            ''')

            # Scrape jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_phase TEXT,
                    total_tweets INTEGER,
                    scraped_tweets INTEGER,
                    total_comments INTEGER,
                    scraped_comments INTEGER,
                    settings TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent_tweet_id ON comments(parent_tweet_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrape_jobs_username ON scrape_jobs(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status)')

    def insert_user(self, user_data):
        """Insert or update user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (
                    user_id, username, display_name, description, location,
                    profile_image_url, profile_banner_url,
                    followers_count, following_count, tweets_count, likes_count,
                    is_verified, is_blue_verified,
                    account_created_at, scraped_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get('user_id'),
                user_data.get('username'),
                user_data.get('display_name'),
                user_data.get('description'),
                user_data.get('location'),
                user_data.get('profile_image_url'),
                user_data.get('profile_banner_url'),
                user_data.get('followers_count'),
                user_data.get('following_count'),
                user_data.get('tweets_count'),
                user_data.get('likes_count'),
                user_data.get('is_verified'),
                user_data.get('is_blue_verified'),
                user_data.get('account_created_at'),
                datetime.utcnow().isoformat(),
                json.dumps(user_data.get('raw_json'))
            ))

    def insert_tweet(self, tweet_data):
        """Insert tweet data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO tweets (
                    tweet_id, user_id, full_text, created_at,
                    retweet_count, favorite_count, reply_count, quote_count, views_count,
                    language, has_media, media_urls, hashtags,
                    scraped_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tweet_data.get('tweet_id'),
                tweet_data.get('user_id'),
                tweet_data.get('full_text'),
                tweet_data.get('created_at'),
                tweet_data.get('retweet_count'),
                tweet_data.get('favorite_count'),
                tweet_data.get('reply_count'),
                tweet_data.get('quote_count'),
                tweet_data.get('views_count'),
                tweet_data.get('language'),
                tweet_data.get('has_media'),
                json.dumps(tweet_data.get('media_urls')) if tweet_data.get('media_urls') else None,
                json.dumps(tweet_data.get('hashtags')) if tweet_data.get('hashtags') else None,
                datetime.utcnow().isoformat(),
                json.dumps(tweet_data.get('raw_json'))
            ))

    def insert_comment(self, comment_data):
        """Insert comment data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO comments (
                    comment_id, parent_tweet_id, user_id, username, display_name,
                    full_text, created_at, favorite_count, reply_count,
                    scraped_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comment_data.get('comment_id'),
                comment_data.get('parent_tweet_id'),
                comment_data.get('user_id'),
                comment_data.get('username'),
                comment_data.get('display_name'),
                comment_data.get('full_text'),
                comment_data.get('created_at'),
                comment_data.get('favorite_count'),
                comment_data.get('reply_count'),
                datetime.utcnow().isoformat(),
                json.dumps(comment_data.get('raw_json'))
            ))

    def create_scrape_job(self, username, settings):
        """Create a new scrape job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scrape_jobs (
                    username, status, current_phase,
                    total_tweets, scraped_tweets, total_comments, scraped_comments,
                    settings, started_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username, 'pending', 'user',
                0, 0, 0, 0,
                json.dumps(settings),
                datetime.utcnow().isoformat()
            ))
            return cursor.lastrowid

    def update_scrape_job(self, job_id, **kwargs):
        """Update scrape job status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                values.append(value)
            values.append(job_id)
            query = f"UPDATE scrape_jobs SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)

    def get_scrape_job(self, job_id):
        """Get scrape job by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scrape_jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_scrape_jobs(self, limit=50):
        """Get all scrape jobs, newest first"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scrape_jobs
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_user_by_username(self, username):
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_tweets_by_user(self, user_id, limit=100):
        """Get tweets by user ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tweets
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_comments_by_tweet(self, tweet_id, limit=100):
        """Get comments by tweet ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM comments
                WHERE parent_tweet_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (tweet_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_scrape_stats(self, job_id):
        """Get statistics for a scrape job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get job details
            cursor.execute('SELECT * FROM scrape_jobs WHERE id = ?', (job_id,))
            job = cursor.fetchone()
            if not job:
                return None

            job_dict = dict(job)
            settings = json.loads(job_dict.get('settings', '{}'))
            username = job_dict.get('username')

            # Get user
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            user_dict = dict(user) if user else None

            # Count tweets
            if user_dict:
                cursor.execute('SELECT COUNT(*) as count FROM tweets WHERE user_id = ?', (user_dict['user_id'],))
                tweet_count = cursor.fetchone()['count']
            else:
                tweet_count = 0

            # Count comments
            cursor.execute('''
                SELECT COUNT(*) as count FROM comments
                WHERE parent_tweet_id IN (
                    SELECT tweet_id FROM tweets WHERE user_id = ?
                )
            ''', (user_dict['user_id'],)) if user_dict else cursor.execute('SELECT 0 as count')
            comment_count = cursor.fetchone()['count']

            return {
                'job': job_dict,
                'user': user_dict,
                'tweet_count': tweet_count,
                'comment_count': comment_count
            }
