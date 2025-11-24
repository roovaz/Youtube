import requests
import time
from datetime import datetime, timedelta
from config import Config
import json


class TwitterScraper:
    """Twitter scraper using Twitter241 RapidAPI"""

    def __init__(self):
        self.api_key = Config.RAPIDAPI_KEY
        self.api_host = Config.RAPIDAPI_HOST
        self.base_url = Config.RAPIDAPI_BASE_URL
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }

    def _make_request(self, endpoint, params=None):
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def get_user_profile(self, username):
        """Get user profile information"""
        response = self._make_request('/user', {'username': username})

        # Parse nested response structure
        try:
            # Try different possible paths for user data
            user_result = None
            if 'result' in response and 'data' in response['result']:
                user_result = response['result']['data'].get('user', {}).get('result', {})
            elif 'data' in response:
                user_result = response['data'].get('user', {}).get('result', {})
            elif 'user' in response:
                user_result = response['user'].get('result', {})

            if not user_result:
                raise Exception("User not found or invalid response structure")

            legacy = user_result.get('legacy', {})
            rest_id = user_result.get('rest_id', '')

            # Check if account is protected
            if legacy.get('protected', False):
                raise Exception("This account is protected/private")

            # Extract profile data
            profile_data = {
                'user_id': rest_id,
                'username': legacy.get('screen_name', username),
                'display_name': legacy.get('name', ''),
                'description': legacy.get('description', ''),
                'location': legacy.get('location', ''),
                'profile_image_url': legacy.get('profile_image_url_https', ''),
                'profile_banner_url': legacy.get('profile_banner_url', ''),
                'followers_count': legacy.get('followers_count', 0),
                'following_count': legacy.get('friends_count', 0),
                'tweets_count': legacy.get('statuses_count', 0),
                'likes_count': legacy.get('favourites_count', 0),
                'is_verified': 1 if legacy.get('verified', False) else 0,
                'is_blue_verified': 1 if user_result.get('is_blue_verified', False) else 0,
                'account_created_at': legacy.get('created_at', ''),
                'raw_json': response
            }

            return profile_data

        except KeyError as e:
            raise Exception(f"Failed to parse user profile: {str(e)}")

    def get_user_tweets(self, username, max_tweets=100, max_age_days=None):
        """Get user tweets with pagination"""
        all_tweets = []
        cursor = None
        cutoff_date = None

        if max_age_days:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        while len(all_tweets) < max_tweets:
            params = {'username': username}
            if cursor:
                params['cursor'] = cursor

            response = self._make_request('/user-tweets', params)

            # Parse tweets from response
            tweets = self._parse_tweets_response(response)

            if not tweets:
                break

            for tweet in tweets:
                # Check tweet age
                if cutoff_date and tweet.get('created_at'):
                    tweet_date = self._parse_twitter_date(tweet['created_at'])
                    if tweet_date and tweet_date < cutoff_date:
                        return all_tweets

                all_tweets.append(tweet)

                if len(all_tweets) >= max_tweets:
                    break

            # Get cursor for next page
            cursor = self._extract_cursor(response)
            if not cursor:
                break

            # Rate limiting delay
            time.sleep(Config.API_DELAY)

        return all_tweets[:max_tweets]

    def get_tweet_comments(self, tweet_id, max_comments=50):
        """Get comments/replies for a tweet"""
        response = self._make_request('/tweet', {'pid': tweet_id})

        comments = self._parse_comments_response(response, tweet_id)

        # Rate limiting delay
        time.sleep(Config.API_DELAY)

        return comments[:max_comments]

    def _parse_tweets_response(self, response):
        """Parse tweets from API response"""
        tweets = []

        try:
            # Navigate through nested structure
            instructions = []
            if 'data' in response and 'user' in response['data']:
                result = response['data']['user'].get('result', {})
                timeline = result.get('timeline_v2', {}).get('timeline', {})
                instructions = timeline.get('instructions', [])
            elif 'timeline' in response:
                instructions = response['timeline'].get('instructions', [])

            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        content = entry.get('content', {})
                        if content.get('entryType') == 'TimelineTimelineItem':
                            item_content = content.get('itemContent', {})
                            tweet_results = item_content.get('tweet_results', {}).get('result', {})

                            if tweet_results and 'legacy' in tweet_results:
                                tweet = self._extract_tweet_data(tweet_results)
                                if tweet:
                                    tweets.append(tweet)

        except Exception as e:
            print(f"Error parsing tweets: {str(e)}")

        return tweets

    def _extract_tweet_data(self, tweet_result):
        """Extract tweet data from result object"""
        try:
            legacy = tweet_result.get('legacy', {})
            core = tweet_result.get('core', {})
            user_results = core.get('user_results', {}).get('result', {})

            # Extract media URLs
            media_urls = []
            entities = legacy.get('entities', {})
            extended_entities = legacy.get('extended_entities', {})
            media = extended_entities.get('media', entities.get('media', []))
            for m in media:
                if 'media_url_https' in m:
                    media_urls.append(m['media_url_https'])

            # Extract hashtags
            hashtags = [ht['text'] for ht in entities.get('hashtags', [])]

            # Get views count
            views_count = tweet_result.get('views', {}).get('count')
            if views_count:
                try:
                    views_count = int(views_count)
                except (ValueError, TypeError):
                    views_count = 0

            tweet_data = {
                'tweet_id': legacy.get('id_str', tweet_result.get('rest_id', '')),
                'user_id': user_results.get('rest_id', ''),
                'full_text': legacy.get('full_text', ''),
                'created_at': legacy.get('created_at', ''),
                'retweet_count': legacy.get('retweet_count', 0),
                'favorite_count': legacy.get('favorite_count', 0),
                'reply_count': legacy.get('reply_count', 0),
                'quote_count': legacy.get('quote_count', 0),
                'views_count': views_count or 0,
                'language': legacy.get('lang', ''),
                'has_media': 1 if media_urls else 0,
                'media_urls': media_urls,
                'hashtags': hashtags,
                'raw_json': tweet_result
            }

            return tweet_data

        except Exception as e:
            print(f"Error extracting tweet data: {str(e)}")
            return None

    def _parse_comments_response(self, response, parent_tweet_id):
        """Parse comments from tweet response"""
        comments = []

        try:
            # Navigate through nested structure
            instructions = []
            if 'data' in response and 'threaded_conversation_with_injections_v2' in response['data']:
                instructions = response['data']['threaded_conversation_with_injections_v2'].get('instructions', [])
            elif 'timeline' in response:
                instructions = response['timeline'].get('instructions', [])

            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        content = entry.get('content', {})
                        if content.get('entryType') == 'TimelineTimelineItem':
                            item_content = content.get('itemContent', {})
                            tweet_results = item_content.get('tweet_results', {}).get('result', {})

                            if tweet_results and 'legacy' in tweet_results:
                                # Skip the original tweet
                                tweet_id = tweet_results.get('legacy', {}).get('id_str', '')
                                if tweet_id != parent_tweet_id:
                                    comment = self._extract_comment_data(tweet_results, parent_tweet_id)
                                    if comment:
                                        comments.append(comment)

        except Exception as e:
            print(f"Error parsing comments: {str(e)}")

        return comments

    def _extract_comment_data(self, tweet_result, parent_tweet_id):
        """Extract comment data from result object"""
        try:
            legacy = tweet_result.get('legacy', {})
            core = tweet_result.get('core', {})
            user_results = core.get('user_results', {}).get('result', {})
            user_legacy = user_results.get('legacy', {})

            comment_data = {
                'comment_id': legacy.get('id_str', tweet_result.get('rest_id', '')),
                'parent_tweet_id': parent_tweet_id,
                'user_id': user_results.get('rest_id', ''),
                'username': user_legacy.get('screen_name', ''),
                'display_name': user_legacy.get('name', ''),
                'full_text': legacy.get('full_text', ''),
                'created_at': legacy.get('created_at', ''),
                'favorite_count': legacy.get('favorite_count', 0),
                'reply_count': legacy.get('reply_count', 0),
                'raw_json': tweet_result
            }

            return comment_data

        except Exception as e:
            print(f"Error extracting comment data: {str(e)}")
            return None

    def _extract_cursor(self, response):
        """Extract pagination cursor from response"""
        try:
            instructions = []
            if 'data' in response and 'user' in response['data']:
                result = response['data']['user'].get('result', {})
                timeline = result.get('timeline_v2', {}).get('timeline', {})
                instructions = timeline.get('instructions', [])
            elif 'timeline' in response:
                instructions = response['timeline'].get('instructions', [])

            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        if 'cursor-bottom' in entry.get('entryId', ''):
                            content = entry.get('content', {})
                            return content.get('value')

        except Exception:
            pass

        return None

    def _parse_twitter_date(self, date_str):
        """Parse Twitter date format to datetime"""
        try:
            # Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
            return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        except Exception:
            return None
