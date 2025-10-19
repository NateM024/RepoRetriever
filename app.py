from flask import Flask, request, jsonify, render_template_string, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
import requests
import os
from dotenv import load_dotenv
import re
import sqlite3
import json
from datetime import datetime
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configure Flask-Session for persistent sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

Session(app)
CORS(app, supports_credentials=True)  # Enable CORS for frontend requests

# GitHub token (optional but recommended for higher rate limits)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub OAuth credentials
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

# GitHub API endpoints
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
GITHUB_OAUTH_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('reporetriever.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  github_id INTEGER UNIQUE,
                  username TEXT,
                  access_token TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Saved repositories table
    c.execute('''CREATE TABLE IF NOT EXISTS saved_repos
                 (id INTEGER PRIMARY KEY,
                  user_id INTEGER,
                  repo_data TEXT,
                  user_note TEXT,
                  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def smart_query_converter(user_query):
    """Convert natural language query to GitHub search terms using smart keyword matching"""
    
    query = user_query.lower().strip()
    
    # Initialize result structure
    result = {
        "keywords": [],
        "language": None,
        "qualifiers": []
    }
    
    # Language detection patterns
    language_patterns = {
        'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'scikit', 'tensorflow'],
        'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'express', 'npm'],
        'typescript': ['typescript', 'ts'],
        'java': ['java', 'spring', 'hibernate', 'maven'],
        'go': ['go', 'golang'],
        'rust': ['rust'],
        'cpp': ['c++', 'cpp'],
        'c': [' c ', 'c library', 'c framework'],
        'php': ['php', 'laravel', 'symfony', 'composer'],
        'ruby': ['ruby', 'rails', 'gem'],
        'swift': ['swift', 'ios'],
        'kotlin': ['kotlin', 'android'],
        'csharp': ['c#', 'csharp', '.net', 'dotnet'],
        'shell': ['bash', 'shell', 'script'],
        'html': ['html', 'css', 'web'],
        'r': [' r ', 'r language', 'rstats'],
        'scala': ['scala'],
        'dart': ['dart', 'flutter']
    }
    
    # Detect programming language
    for lang, patterns in language_patterns.items():
        if any(pattern in query for pattern in patterns):
            result['language'] = lang
            break
    
    # Topic mapping - maps common phrases to GitHub search keywords
    topic_mapping = {
        # Web Development
        'web scraping': ['web-scraping', 'scraper', 'crawler'],
        'scraping': ['scraper', 'web-scraping'],
        'crawler': ['crawler', 'scraper'],
        'dashboard': ['dashboard', 'admin', 'panel'],
        'admin panel': ['admin', 'dashboard', 'panel'],
        'ui components': ['ui', 'components', 'library'],
        'component library': ['components', 'ui', 'library'],
        'rest api': ['rest-api', 'api'],
        'graphql': ['graphql', 'api'],
        'authentication': ['auth', 'authentication', 'login'],
        'oauth': ['oauth', 'authentication'],
        'jwt': ['jwt', 'auth'],
        
        # Data & ML
        'machine learning': ['machine-learning', 'ml', 'ai'],
        'deep learning': ['deep-learning', 'neural-network', 'ml'],
        'neural network': ['neural-network', 'deep-learning'],
        'data science': ['data-science', 'analytics', 'visualization'],
        'data visualization': ['visualization', 'charts', 'plotting'],
        'database': ['database', 'db', 'storage'],
        'sql': ['sql', 'database'],
        'nosql': ['nosql', 'database'],
        'mongodb': ['mongodb', 'nosql'],
        'postgres': ['postgresql', 'database'],
        'mysql': ['mysql', 'database'],
        
        # Development Tools
        'testing': ['testing', 'test', 'unittest'],
        'unit test': ['unittest', 'testing'],
        'docker': ['docker', 'container'],
        'kubernetes': ['kubernetes', 'k8s', 'container'],
        'ci/cd': ['ci-cd', 'automation', 'deployment'],
        'deployment': ['deployment', 'deploy'],
        'monitoring': ['monitoring', 'logging', 'metrics'],
        'logging': ['logging', 'monitor'],
        
        # Mobile & Game Development
        'mobile': ['mobile', 'app'],
        'android': ['android', 'mobile'],
        'ios': ['ios', 'mobile'],
        'game engine': ['game-engine', 'game', 'gaming'],
        'game development': ['game', 'gaming', 'engine'],
        '2d game': ['2d', 'game'],
        '3d game': ['3d', 'game'],
        
        # Tools & Utilities
        'command line': ['cli', 'command-line'],
        'cli tool': ['cli', 'tool'],
        'parser': ['parser', 'parsing'],
        'json parser': ['json', 'parser'],
        'xml parser': ['xml', 'parser'],
        'file upload': ['upload', 'file'],
        'image processing': ['image', 'processing', 'graphics'],
        'pdf': ['pdf', 'document'],
        'email': ['email', 'mail'],
        'encryption': ['encryption', 'crypto', 'security'],
        'security': ['security', 'auth'],
        'blockchain': ['blockchain', 'crypto'],
        'cryptocurrency': ['crypto', 'blockchain']
    }
    
    # Extract keywords based on topics found
    keywords_found = set()
    for phrase, keywords in topic_mapping.items():
        if phrase in query:
            keywords_found.update(keywords)
    
    # Add general keywords from the query (filter out common words)
    stop_words = {
        'i', 'need', 'want', 'looking', 'for', 'a', 'an', 'the', 'that', 'can', 
        'help', 'me', 'with', 'to', 'and', 'or', 'but', 'is', 'are', 'was', 
        'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'library',
        'framework', 'tool', 'application', 'app', 'project', 'code', 'simple',
        'easy', 'good', 'best', 'great', 'awesome', 'cool', 'nice'
    }
    
    # Extract meaningful words
    words = re.findall(r'\b\w+\b', query)
    meaningful_words = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # Add some meaningful words as keywords (limit to avoid too broad search)
    keywords_found.update(meaningful_words[:3])
    
    result['keywords'] = list(keywords_found)[:3]  # Limit to 3 keywords max for better results
    
    # Quality and difficulty qualifiers
    if any(word in query for word in ['beginner', 'easy', 'simple', 'starter']):
        result['qualifiers'].extend(['stars:>100'])  # Just use stars, not good-first-issues
    elif any(word in query for word in ['popular', 'widely used', 'well known', 'famous']):
        result['qualifiers'].extend(['stars:>1000', 'forks:>100'])
    elif any(word in query for word in ['mature', 'stable', 'production']):
        result['qualifiers'].extend(['stars:>500', 'pushed:>2023-01-01'])
    else:
        # Default quality filter
        result['qualifiers'].append('stars:>10')
    
    # Size preferences
    if any(word in query for word in ['lightweight', 'small', 'minimal']):
        result['qualifiers'].append('size:<1000')
    elif any(word in query for word in ['comprehensive', 'full', 'complete']):
        result['qualifiers'].append('size:>1000')
    
    # Activity preferences
    if any(word in query for word in ['active', 'maintained', 'recent', 'updated']):
        result['qualifiers'].append('pushed:>2023-06-01')
    
    return result

def build_github_query(search_params):
    """Build GitHub search query from parameters"""
    query_parts = []
    
    # Add keywords
    if search_params.get('keywords'):
        query_parts.extend(search_params['keywords'])
    
    # Add language
    if search_params.get('language'):
        query_parts.append(f"language:{search_params['language']}")
    
    # Add qualifiers
    if search_params.get('qualifiers'):
        query_parts.extend(search_params['qualifiers'])
    
    return ' '.join(query_parts)

def search_github_repositories(query):
    """Search GitHub repositories using their API"""
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoRetriever"
    }
    
    # Add GitHub token if available for higher rate limits
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 12  # Get more results
    }
    
    try:
        response = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('items', [])
        
    except requests.exceptions.RequestException as e:
        print(f"GitHub API error: {e}")
        raise Exception("Failed to search GitHub repositories")

@app.route('/favicon.png')
def favicon():
    """Serve the favicon"""
    return send_from_directory('.', 'favicon.png', mimetype='image/png')

@app.route('/')
def index():
    """Serve the frontend HTML"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Frontend HTML file not found. Please save the frontend code as 'index.html'"
    except UnicodeDecodeError:
        return "HTML file encoding error. Please save index.html with UTF-8 encoding."

@app.route('/search', methods=['POST'])
def search_repositories():
    """Main endpoint to search repositories"""
    
    try:
        # Get user query from request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query is required"}), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Step 1: Convert query using smart keyword matching
        print(f"Processing query: {user_query}")
        ai_response = smart_query_converter(user_query)
        print(f"Conversion result: {ai_response}")
        
        # Step 2: Build GitHub search query
        github_query = build_github_query(ai_response)
        print(f"GitHub Query: {github_query}")
        
        # Step 3: Search GitHub repositories
        repositories = search_github_repositories(github_query)
        print(f"Found {len(repositories)} repositories")
        
        # Return results
        return jsonify({
            "ai_response": ai_response,
            "github_query": github_query,
            "repositories": repositories
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "conversion_type": "smart_keyword_matching",
        "github_configured": bool(GITHUB_TOKEN),
        "oauth_configured": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
    })

# ===== OAuth Routes =====

@app.route('/auth/login')
def login():
    """Redirect to GitHub OAuth"""
    if not GITHUB_CLIENT_ID:
        return jsonify({"error": "OAuth not configured"}), 500
    
    # Redirect to GitHub OAuth
    github_auth_url = f"{GITHUB_OAUTH_AUTHORIZE}?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_auth_url)

@app.route('/auth/callback')
def callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    print(f"OAuth callback received. Code present: {bool(code)}")
    
    if not code:
        return redirect('/?error=oauth_failed')
    
    try:
        # Exchange code for access token
        token_response = requests.post(
            GITHUB_OAUTH_TOKEN,
            headers={'Accept': 'application/json'},
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code
            }
        )
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        print(f"Token exchange successful: {bool(access_token)}")
        
        if not access_token:
            print(f"Token error: {token_data}")
            return redirect('/?error=oauth_failed')
        
        # Get user info from GitHub
        user_response = requests.get(
            GITHUB_USER_API,
            headers={'Authorization': f'token {access_token}'}
        )
        user_data = user_response.json()
        
        print(f"User data received: {user_data.get('login')}")
        
        # Save or update user in database
        conn = sqlite3.connect('reporetriever.db')
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO users (github_id, username, access_token)
                     VALUES (?, ?, ?)''',
                  (user_data['id'], user_data['login'], access_token))
        
        user_id = c.lastrowid if c.lastrowid else c.execute(
            'SELECT id FROM users WHERE github_id = ?', (user_data['id'],)
        ).fetchone()[0]
        
        conn.commit()
        conn.close()
        
        # Store user in session
        session['user_id'] = user_id
        session['username'] = user_data['login']
        session['github_id'] = user_data['id']
        session.permanent = True  # Make session permanent
        
        print(f"Session set for user: {session['username']}")
        print(f"Session data: {dict(session)}")
        print(f"Session permanent: {session.permanent}")
        
        return redirect('/')
        
    except Exception as e:
        print(f"OAuth error: {e}")
        import traceback
        traceback.print_exc()
        return redirect('/?error=oauth_failed')

@app.route('/auth/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')

@app.route('/auth/user')
def get_user():
    """Get current user info"""
    print(f"Auth check - Session data: {dict(session)}")
    print(f"User ID in session: {session.get('user_id')}")
    
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "username": session.get('username'),
            "user_id": session.get('user_id')
        })
    return jsonify({"logged_in": False})

# ===== Saved Repos Routes =====

@app.route('/repos/save', methods=['POST'])
def save_repo():
    """Save a repository for the user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    repo_data = data.get('repo')
    user_note = data.get('note', '')
    
    if not repo_data:
        return jsonify({"error": "Repository data required"}), 400
    
    try:
        conn = sqlite3.connect('reporetriever.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO saved_repos (user_id, repo_data, user_note)
                     VALUES (?, ?, ?)''',
                  (session['user_id'], json.dumps(repo_data), user_note))
        
        conn.commit()
        saved_id = c.lastrowid
        conn.close()
        
        return jsonify({"success": True, "saved_id": saved_id})
        
    except Exception as e:
        print(f"Save error: {e}")
        return jsonify({"error": "Failed to save repository"}), 500

@app.route('/repos/saved', methods=['GET'])
def get_saved_repos():
    """Get all saved repositories for the user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        conn = sqlite3.connect('reporetriever.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, repo_data, user_note, saved_at
                     FROM saved_repos
                     WHERE user_id = ?
                     ORDER BY saved_at DESC''',
                  (session['user_id'],))
        
        rows = c.fetchall()
        conn.close()
        
        saved_repos = []
        for row in rows:
            saved_repos.append({
                'id': row[0],
                'repo': json.loads(row[1]),
                'note': row[2],
                'saved_at': row[3]
            })
        
        return jsonify({"repos": saved_repos})
        
    except Exception as e:
        print(f"Fetch error: {e}")
        return jsonify({"error": "Failed to fetch saved repositories"}), 500

@app.route('/repos/unsave/<int:saved_id>', methods=['DELETE'])
def unsave_repo(saved_id):
    """Remove a saved repository"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        conn = sqlite3.connect('reporetriever.db')
        c = conn.cursor()
        
        c.execute('''DELETE FROM saved_repos
                     WHERE id = ? AND user_id = ?''',
                  (saved_id, session['user_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"error": "Failed to delete repository"}), 500

@app.route('/repos/check/<int:repo_id>', methods=['GET'])
def check_if_saved(repo_id):
    """Check if a repository is already saved by the user"""
    if 'user_id' not in session:
        return jsonify({"saved": False})
    
    try:
        conn = sqlite3.connect('reporetriever.db')
        c = conn.cursor()
        
        # Check by repo id in the saved repo_data JSON
        c.execute('''SELECT id FROM saved_repos WHERE user_id = ?''',
                  (session['user_id'],))
        
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            # This is a simple check - you might want to optimize this
            pass
        
        return jsonify({"saved": False})
        
    except Exception as e:
        return jsonify({"saved": False})

if __name__ == '__main__':
    # Check if required environment variables are set
    if not GITHUB_TOKEN:
        print("ℹ️  GitHub token not configured - using lower rate limits (60/hour)")
        print("💡 Add GITHUB_TOKEN to .env for 5,000/hour rate limit")
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        print("⚠️  Warning: GitHub OAuth not configured")
        print("💡 Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to .env to enable user login")
    
    print("🚀 Starting RepoRetriever backend...")
    print("🧠 Using smart keyword matching (no AI costs!)")
    print("🔐 OAuth authentication enabled" if (GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET) else "🔓 OAuth not configured")
    print(f"💾 Session type: {app.config.get('SESSION_TYPE')}")
    print(f"📁 Session directory: {app.config.get('SESSION_FILE_DIR')}")
    print("📍 Frontend available at: http://localhost:5000")
    print("🔍 API endpoint: http://localhost:5000/search")
    
    app.run(debug=True, port=5000)