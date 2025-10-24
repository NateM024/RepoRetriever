# RepoRetriever 🔍

**Smart GitHub repository finder that converts natural language queries into optimized GitHub search terms.**

Stop struggling with GitHub's search syntax! Just describe what you're looking for in plain English and RepoRetriever will find the perfect repositories for you.

## ✨ Features

- 🧠 **Smart Query Conversion**: Converts natural language to GitHub search terms
- 🎯 **Language Detection**: Automatically detects programming languages mentioned
- ⚡ **Quality Filtering**: Adds appropriate stars/activity filters based on your needs
- 🚀 **No AI Costs**: Uses intelligent keyword matching (no API fees!)
- 📱 **Clean Interface**: Simple, responsive web interface
- 🔒 **Secure**: API keys stored safely in environment variables

## 🎬 Demo

**Input:** "Python web scraping library for beginners"  
**Output:** `language:python web-scraping scraper crawler good-first-issues:>1 stars:>50`

**Input:** "Popular React dashboard components"  
**Output:** `language:javascript dashboard admin ui components stars:>1000 forks:>100`

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/RepoRetriever.git
   cd RepoRetriever
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "GITHUB_TOKEN=your_github_token_here" > .env
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:5000`

## 🔧 Setup Details

### GitHub Token (Recommended)
While optional, a GitHub token increases your rate limit from 60 to 5,000 requests per hour.

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Generate a new **Classic** token
3. **No scopes needed** (we only search public repositories)
4. Add it to your `.env` file

### Environment Variables
Create a `.env` file in the project root:
```env
# GitHub token for higher rate limits (optional but recommended)
GITHUB_TOKEN=your_github_token_here
```

## 🎯 Example Queries

Try these natural language searches:

- `"Python machine learning for beginners"`
- `"React components for building dashboards"`
- `"JavaScript game engine for 2D games"`
- `"Docker configuration for Node.js"`
- `"Popular web scraping tools"`
- `"Lightweight JSON parser"`
- `"Active authentication library"`

## 🧠 How It Works

RepoRetriever uses intelligent keyword matching to convert your natural language into GitHub search parameters:

1. **Language Detection**: Recognizes mentions of Python, JavaScript, Java, etc.
2. **Topic Mapping**: Maps phrases like "web scraping" to relevant keywords
3. **Quality Filters**: Adds appropriate filters based on words like "beginner", "popular", "maintained"
4. **GitHub Search**: Executes optimized search using GitHub's API

## 📁 Project Structure

```
RepoRetriever/
├── app.py              # Flask backend with smart conversion logic
├── index.html          # Frontend web interface
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-CORS
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: GitHub Search API
- **Smart Conversion**: Custom keyword matching algorithm

## 🔍 API Endpoints

- `GET /` - Main web interface
- `POST /search` - Search repositories
  ```json
  {
    "query": "Python web scraping for beginners"
  }
  ```
- `GET /health` - Health check

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GitHub API for providing repository data
- Flask community for the excellent web framework
- Claude (Anthropic) for pair programming and development assistance
- All the amazing open source projects that make development possible

## 🐛 Issues & Feature Requests

Found a bug or have a feature idea? Please [open an issue](https://github.com/yourusername/RepoRetriever/issues)!

---

**Made with ❤️ by NateM024**

*Happy repository hunting!* 🎯
