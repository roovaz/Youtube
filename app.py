from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import threading
import time
import json
import csv
import io
from datetime import datetime
from database import Database
from scraper import TwitterScraper
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database
db = Database()
db.init_db()

# Global dictionary to store job progress
job_progress = {}
job_locks = {}


def scrape_twitter_job(job_id, username, settings):
    """Background job to scrape Twitter profile"""
    scraper = TwitterScraper()

    try:
        # Update job status
        db.update_scrape_job(job_id, status='running', current_phase='user')
        job_progress[job_id] = {
            'phase': 'user',
            'status': 'running',
            'message': 'Fetching user profile...',
            'tweets_scraped': 0,
            'tweets_total': settings['max_tweets'],
            'comments_scraped': 0,
            'comments_total': 0
        }

        # Step 1: Fetch user profile
        user_data = scraper.get_user_profile(username)
        db.insert_user(user_data)

        job_progress[job_id].update({
            'phase': 'tweets',
            'message': 'User profile fetched. Scraping tweets...',
            'user_data': {
                'display_name': user_data['display_name'],
                'username': user_data['username'],
                'followers_count': user_data['followers_count'],
                'profile_image_url': user_data['profile_image_url']
            }
        })
        db.update_scrape_job(job_id, current_phase='tweets')

        # Step 2: Fetch tweets
        tweets = scraper.get_user_tweets(
            username,
            max_tweets=settings['max_tweets'],
            max_age_days=settings.get('max_age_days')
        )

        for i, tweet in enumerate(tweets):
            tweet['user_id'] = user_data['user_id']
            db.insert_tweet(tweet)

            job_progress[job_id].update({
                'tweets_scraped': i + 1,
                'message': f'Scraped {i + 1}/{len(tweets)} tweets...'
            })

        db.update_scrape_job(
            job_id,
            total_tweets=len(tweets),
            scraped_tweets=len(tweets)
        )

        # Step 3: Fetch comments
        if settings['max_comments'] > 0:
            job_progress[job_id].update({
                'phase': 'comments',
                'message': 'Scraping comments...',
                'comments_total': len(tweets) * settings['max_comments']
            })
            db.update_scrape_job(job_id, current_phase='comments')

            total_comments = 0
            for i, tweet in enumerate(tweets):
                comments = scraper.get_tweet_comments(
                    tweet['tweet_id'],
                    max_comments=settings['max_comments']
                )

                for comment in comments:
                    db.insert_comment(comment)
                    total_comments += 1

                job_progress[job_id].update({
                    'tweets_scraped': i + 1,
                    'comments_scraped': total_comments,
                    'message': f'Scraped comments for {i + 1}/{len(tweets)} tweets...'
                })

            db.update_scrape_job(
                job_id,
                total_comments=total_comments,
                scraped_comments=total_comments
            )
        else:
            db.update_scrape_job(
                job_id,
                total_comments=0,
                scraped_comments=0
            )

        # Complete job
        db.update_scrape_job(
            job_id,
            status='completed',
            completed_at=datetime.utcnow().isoformat()
        )
        job_progress[job_id].update({
            'phase': 'completed',
            'status': 'completed',
            'message': 'Scraping completed successfully!'
        })

    except Exception as e:
        error_msg = str(e)
        db.update_scrape_job(
            job_id,
            status='failed',
            error_message=error_msg,
            completed_at=datetime.utcnow().isoformat()
        )
        job_progress[job_id].update({
            'status': 'failed',
            'message': f'Error: {error_msg}'
        })


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'ok'})


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start a new scrape job"""
    data = request.json

    username = data.get('username', '').strip().replace('@', '')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    settings = {
        'max_tweets': int(data.get('max_tweets', Config.DEFAULT_MAX_TWEETS)),
        'max_age_days': data.get('max_age_days'),
        'max_comments': int(data.get('max_comments', Config.DEFAULT_MAX_COMMENTS))
    }

    # Validate settings
    if settings['max_tweets'] < 1 or settings['max_tweets'] > 500:
        return jsonify({'error': 'Max tweets must be between 1 and 500'}), 400

    if settings['max_comments'] < 0 or settings['max_comments'] > 100:
        return jsonify({'error': 'Max comments must be between 0 and 100'}), 400

    # Create job
    job_id = db.create_scrape_job(username, settings)
    job_locks[job_id] = threading.Lock()

    # Start background thread
    thread = threading.Thread(
        target=scrape_twitter_job,
        args=(job_id, username, settings)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'job_id': job_id,
        'message': 'Scraping started'
    })


@app.route('/api/stream/<int:job_id>')
def stream_progress(job_id):
    """Server-Sent Events endpoint for progress updates"""
    def generate():
        last_update = None
        timeout = 0
        max_timeout = 600  # 10 minutes

        while timeout < max_timeout:
            current_progress = job_progress.get(job_id)

            if current_progress:
                # Send update if changed
                if current_progress != last_update:
                    yield f"data: {json.dumps(current_progress)}\n\n"
                    last_update = current_progress.copy()

                # Check if completed or failed
                if current_progress.get('status') in ['completed', 'failed']:
                    break

            time.sleep(0.5)
            timeout += 0.5

        # Send final update
        if job_id in job_progress:
            yield f"data: {json.dumps(job_progress[job_id])}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/job/<int:job_id>')
def get_job(job_id):
    """Get job details and statistics"""
    stats = db.get_scrape_stats(job_id)
    if not stats:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(stats)


@app.route('/api/jobs')
def get_jobs():
    """Get all jobs"""
    jobs = db.get_all_scrape_jobs()
    return jsonify(jobs)


@app.route('/api/export/<int:job_id>/<format>')
def export_data(job_id, format):
    """Export job data as JSON or CSV"""
    stats = db.get_scrape_stats(job_id)
    if not stats:
        return jsonify({'error': 'Job not found'}), 404

    user = stats['user']
    if not user:
        return jsonify({'error': 'No data to export'}), 404

    tweets = db.get_tweets_by_user(user['user_id'])

    if format == 'json':
        data = {
            'user': user,
            'tweets': tweets,
            'export_date': datetime.utcnow().isoformat()
        }
        return Response(
            json.dumps(data, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={user["username"]}_data.json'
            }
        )

    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'tweet_id', 'full_text', 'created_at', 'retweet_count',
            'favorite_count', 'reply_count', 'quote_count', 'views_count'
        ])

        # Write tweets
        for tweet in tweets:
            writer.writerow([
                tweet['tweet_id'],
                tweet['full_text'],
                tweet['created_at'],
                tweet['retweet_count'],
                tweet['favorite_count'],
                tweet['reply_count'],
                tweet['quote_count'],
                tweet['views_count']
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={user["username"]}_tweets.csv'
            }
        )

    return jsonify({'error': 'Invalid format'}), 400


@app.route('/api/cancel/<int:job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    if job_id in job_progress:
        job_progress[job_id].update({
            'status': 'cancelled',
            'message': 'Job cancelled by user'
        })
        db.update_scrape_job(
            job_id,
            status='failed',
            error_message='Cancelled by user',
            completed_at=datetime.utcnow().isoformat()
        )
        return jsonify({'message': 'Job cancelled'})

    return jsonify({'error': 'Job not found'}), 404


if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the RAPIDAPI_KEY environment variable")
        exit(1)

    app.run(debug=True, host='0.0.0.0', port=5000)
