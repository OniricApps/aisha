# Aisha - AI Shopping Assistant

Version 0.7.0

## Overview

Aisha is a personal shopping assistant chatbot that helps users find products on Amazon and other online stores. Built with Flask and powered by Google's Gemini AI (via DSPy), Aisha provides conversational product recommendations, gift ideas, and personalized shopping assistance in Spanish.

An [OniricApps](https://oniricapps.com) production.

## Try it online!

Demo site [aisha-on.com](https://aisha-on.com).

## Features
- 🤖 **Conversational AI Shopping Assistant**: Natural language interaction for product searches
- 🏬 **Multi-Store Integration**: Primary integration with Amazon (extensible to other stores)
- 🔎 **Product Search & Recommendations**: Find products based on user requirements
- 🎁 **Gift Ideas**: Suggest appropriate gifts based on recipient and occasion
- 💬 **Chat History**: Persistent chat sessions with automatic titling
- 💸 **Affiliate Integration**: Amazon affiliate links for monetization
- 📊 **Statistics Dashboard**: Track usage, referrers, and chat analytics
- 🗄️ **Caching System**: Efficient API query caching to reduce costs


## Architecture

### Core Components

- **app.py**: Flask web application with routing and session management
- **chat.py**: Main chatbot logic using DSPy and Gemini AI
- **amazon_api.py**: Amazon Product Advertising API and Apify integration
- **caches.py**: Cache management for API queries, bot queries, and chat history
- **stats.py**: Analytics and statistics generation
- **cron.py**: Maintenance tasks for chat cleanup and management

### Technology Stack

- **Backend**: Flask 3.1.2
- **AI/ML**: DSPy 2.5.54, Google Generative AI (Gemini 2.5 Flash Lite)
- **APIs**: 
  - Amazon Product Advertising API (python-amazon-paapi)
  - Apify for advanced Amazon scraping
- **Frontend**: Jinja2 templates, vanilla JavaScript
- **Data Processing**: Pandas, CSV and JSON files

## Prerequisites

- Python 3.8+
- Amazon Product Advertising API credentials (Access Key, Secret Key)
- Amazon Affiliate Tag
- Google Gemini API Key
- Apify API Token (for advanced searches)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/OniricApps/aisha
cd aisha
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

You need to configure the following API keys in the respective files:

#### amazon_api.py
```python
AMAZON_AFFILIATE_TAG = 'your-affiliate-tag'
API_TOKEN = 'your-apify-api-token'
ACCESS_KEY = 'your-amazon-access-key'
SECRET_KEY = 'your-amazon-secret-key'
```

#### chat.py
```python
GEMINI_API_KEY = 'your-gemini-api-key'
```

#### app.py
```python
app.secret_key = 'your-secure-secret-key'
```

**⚠️ IMPORTANT FOR PRODUCTION**: 
- Never commit API keys to version control
- Use environment variables or a secrets management system
- Create a `secrets.py` file (already in .gitignore) and import from there

### 4. Create Required Directories

The application will automatically create necessary directories on first run:
- `cache/api_queries/`
- `cache/bot_queries/`
- `cache/chat/`
- `cache/out_links/`
- `logs/`

## Configuration

### Environment Setup Example

Create a `secrets.py` file (not tracked by git):

```python
# secrets.py
AMAZON_AFFILIATE_TAG = 'your-affiliate-tag'
APIFY_API_TOKEN = 'your-apify-token'
AMAZON_ACCESS_KEY = 'your-access-key'
AMAZON_SECRET_KEY = 'your-secret-key'
GEMINI_API_KEY = 'your-gemini-key'
FLASK_SECRET_KEY = 'your-flask-secret'
```

Then import in your main files:

```python
from secrets import AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, ...
```

## Running the Application

### Development Mode

```bash
python app.py
```

The application will start on `http://0.0.0.0:5009`

### Production Mode

Use the provided scripts in the `scripts/` directory:

```bash
# Start the application
./scripts/run.sh

# Stop the application
./scripts/stop.sh

# Restart the application
./scripts/restart.sh
```

### Cron Jobs

Set up automated maintenance tasks:

```bash
# Add to crontab
crontab -e

# Example: Run maintenance daily at 3 AM
0 3 * * * /path/to/project/scripts/cron.sh
```

## Usage

### Web Interface

1. Navigate to `http://localhost:5009`
2. Start a new chat or view previous interesting chats
3. Ask for product recommendations in natural language
4. Browse suggested products with Amazon affiliate links

### API Endpoints

- `GET /`: Home page with recent interesting chats
- `GET /new-chat`: Start a new chat session
- `GET /chat?chat_id=<id>`: View specific chat
- `GET /get?msg=<message>&chat_id=<id>`: Send message to chatbot
- `GET /get-history?chat_id=<id>&index=<n>`: Retrieve chat history
- `GET /product-list?query_id=<id>`: Get product list for a query
- `GET /chats-list`: View all interesting chats
- `GET /stats`: View analytics dashboard (admin)
- `GET /cron`: Trigger maintenance tasks
- `GET /out?link_id=<id>`: Track outbound link clicks

## Project Structure

```
.
├── app.py                  # Flask application and routes
├── chat.py                 # Chatbot logic and AI integration
├── amazon_api.py           # Amazon API integration
├── caches.py              # Cache management
├── stats.py               # Analytics and statistics
├── cron.py                # Maintenance tasks
├── requirements.txt       # Python dependencies
├── cache/                 # Cached data (not in git)
│   ├── api_queries/      # Amazon API query results
│   ├── bot_queries/      # Bot query cache
│   ├── chat/             # Chat history
│   └── out_links/        # Outbound link tracking
├── logs/                  # Application logs (not in git)
│   ├── chatbot.txt       # Chatbot activity log
│   ├── requests-log.csv  # HTTP request logs
│   └── pid.txt           # Process ID file
├── static/               # Static assets (CSS)
├── templates/            # Jinja2 HTML templates
└── scripts/              # Deployment and maintenance scripts
```

## Features in Detail

### Chat States

The chatbot operates in different conversational states:
- **Hello**: Initial greeting
- **Product**: Direct product query
- **Ideas**: Brainstorming gift/product ideas
- **Refinement**: Refining search criteria
- **No_Product**: Cannot find suitable products

### Caching System

The application implements multi-level caching:
- **API Query Cache**: Stores Amazon API responses to avoid redundant calls
- **Bot Query Cache**: Caches processed bot queries
- **Chat Cache**: Persistent chat history storage
- **Out Link Cache**: Tracks affiliate link clicks

### Statistics

The stats module provides:
- Daily page views and visitor counts
- Chat creation metrics
- Referrer analysis
- Conversion ratios

## Maintenance

### Chat Cleanup

Automatic maintenance (via cron) includes:
- Closing inactive chats
- Removing uninteresting chats (no meaningful interaction)
- Generating titles for new chats

### Log Management

Logs accumulate in the `logs/` directory:
- `requests-log.csv`: All HTTP requests
- `chatbot.txt`: Chatbot activity
- Clean up old logs periodically to save disk space

## Development

### Adding New Stores

To integrate additional online stores:

1. Create a new API class in `amazon_api.py` (or separate file)
2. Implement search and product retrieval methods
3. Update the `PROMPT_STORES` in `chat.py`
4. Modify chatbot logic to route queries to appropriate store

### Customizing AI Behavior

The chatbot behavior is controlled by prompts in `chat.py`:
- `PROMPT_GENERAL`: Base personality and role
- `PROMPT_STORES`: Available stores
- `state_description`: Conversation state definitions

Modify these to change the assistant's personality and capabilities.

## Security Considerations

⚠️ **Before deploying to production:**

1. **API Keys**: Move all API keys to environment variables or secure secrets management
2. **Flask Secret Key**: Generate a strong random secret key
3. **HTTPS**: Always use HTTPS in production
4. **Input Validation**: Review all user input handling
5. **Rate Limiting**: Consider adding rate limiting to prevent abuse
6. **Access Control**: Protect admin endpoints (/stats, /cron)

## Known Issues & TODOs

From code comments:
- Implement async search for better performance
- Add file locking for cache writes to prevent conflicts
- Convert `/get` endpoint from GET to POST for longer queries
- Implement proper authentication for session validation
- Consider WebSocket for real-time chat updates

## Contributing

When contributing to this project:
1. Never commit API keys or secrets
2. Follow existing code style
3. Update documentation for new features
4. Test thoroughly with different query types

## License

GNU General Public License v3.0

## Contact

An [OniricApps](https://oniricapps.com) production.

## Try it online!

Demo site: [aisha - **a**rtificial **i**ntelligence personal **sh**opping **a**ssistant](https://aisha-on.com).

## Acknowledgments

- Built with Flask and DSPy
- Powered by Google Gemini AI
- Amazon Product Advertising API
- Apify for advanced scraping capabilities
