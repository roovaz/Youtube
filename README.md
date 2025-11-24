# Twitter/X Profile Scraper

A web application that scrapes Twitter/X profiles using the Twitter241 RapidAPI. Built with Flask, SQLite, and Tailwind CSS.

## Features

- Scrape user profiles with detailed information
- Collect tweets with configurable limits and age filters
- Scrape comments/replies on tweets
- Real-time progress updates using Server-Sent Events
- Export data as JSON or CSV
- View scrape history
- Mobile-responsive dark theme UI

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **API**: Twitter241 RapidAPI
- **Deployment**: Railway.app

## Project Structure

```
/
├── app.py              # Flask application with routes and SSE
├── database.py         # SQLite database manager
├── scraper.py          # Twitter241 API client
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment config
├── runtime.txt        # Python version
├── .gitignore         # Git ignore rules
└── templates/
    └── index.html     # Web UI
```

## Database Schema

### Tables

1. **users** - User profile information
2. **tweets** - Tweet data with engagement metrics
3. **comments** - Comments/replies on tweets
4. **scrape_jobs** - Scrape job tracking and status

## Setup

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd Youtube
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export RAPIDAPI_KEY="your-rapidapi-key"
export SECRET_KEY="your-secret-key"
```

5. Run the application:
```bash
python app.py
```

6. Open your browser to `http://localhost:5000`

### Railway Deployment

1. Connect your GitHub repository to Railway

2. Set environment variables in Railway dashboard:
   - `RAPIDAPI_KEY`: Your Twitter241 RapidAPI key
   - `SECRET_KEY`: Random string for Flask sessions

3. Deploy! Railway will automatically detect the Procfile and deploy.

## Environment Variables

| Variable      | Description                          | Required |
|--------------|--------------------------------------|----------|
| RAPIDAPI_KEY | Twitter241 RapidAPI key             | Yes      |
| SECRET_KEY   | Flask secret key for sessions       | Yes      |
| DATABASE_PATH| Path to SQLite database (optional)  | No       |

## API Endpoints

- `GET /` - Main web interface
- `GET /health` - Health check endpoint
- `POST /api/scrape` - Start a new scrape job
- `GET /api/stream/<job_id>` - SSE endpoint for progress updates
- `GET /api/job/<job_id>` - Get job details and statistics
- `GET /api/jobs` - Get all scrape jobs
- `GET /api/export/<job_id>/<format>` - Export data (json/csv)
- `POST /api/cancel/<job_id>` - Cancel a running job

## Usage

1. Enter a Twitter username (with or without @)
2. Configure scraping settings:
   - Max tweets (10-500)
   - Max tweet age (7-90 days or unlimited)
   - Max comments per tweet (0-100)
3. Click "Start Scraping"
4. Watch real-time progress
5. Export results as JSON or CSV

## Features Details

### Real-time Progress
- Server-Sent Events (SSE) for live updates
- Phase indicators (Profile → Tweets → Comments)
- Progress bars with counters
- Cancel functionality

### Data Collection
- User profile with stats
- Tweet text, timestamps, and engagement metrics
- Comments with user info
- Raw JSON stored for future parsing

### Export Options
- **JSON**: Complete data including nested structures
- **CSV**: Flat tweet data for spreadsheet analysis

## Rate Limiting

The scraper includes a 0.5-second delay between API calls to respect rate limits.

## Error Handling

- User not found
- Protected/private accounts
- API errors and rate limits
- Network timeouts

## Notes

- SQLite database is ephemeral on Railway (resets on deployment)
- For persistent storage, consider using Railway's PostgreSQL addon
- API responses are stored as raw JSON for future extensibility

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues or questions, please open an issue on GitHub.
