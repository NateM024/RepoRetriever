from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# GitHub token (optional but recommended for higher rate limits)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub API endpoint
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

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
    
    result['keywords'] = list(keywords_found)[:6]  # Limit to 6 keywords max
    
    # Quality and difficulty qualifiers
    if any(word in query for word in ['beginner', 'easy', 'simple', 'starter']):
        result['qualifiers'].extend(['good-first-issues:>1', 'stars:>50'])
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
        "github_configured": bool(GITHUB_TOKEN)
    })

if __name__ == '__main__':
    if not GITHUB_TOKEN:
        print("ℹ️  GitHub token not configured - using lower rate limits (60/hour)")
        print("💡 Add GITHUB_TOKEN to .env for 5,000/hour rate limit")
    
    print("🚀 Starting RepoRetriever backend...")
    print("🧠 Using smart keyword matching (no AI costs!)")
    print("📍 Frontend available at: http://localhost:5000")
    print("🔍 API endpoint: http://localhost:5000/search")
    
    app.run(debug=True, port=5000)