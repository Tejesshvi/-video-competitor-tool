# ─────────────────────────────────────────────────────────────────────────────
# Video Competitor Intelligence Tool — MyPromoVideos Round 2
# ─────────────────────────────────────────────────────────────────────────────

## QUICK START

### 1. Get a YouTube Data API v3 Key
1. Go to https://console.cloud.google.com/
2. Create a project → Enable "YouTube Data API v3"
3. Credentials → Create API Key → Copy it

### 2. Install dependencies
```
pip install flask requests python-pptx isodate
```

### 3. Run the app
**Windows PowerShell:**
```powershell
$env:YOUTUBE_API_KEY="YOUR_API_KEY_HERE"
python app.py
```

**Or with a .env file — create `app/.env`:**
```
YOUTUBE_API_KEY=YOUR_API_KEY_HERE
```
Then run: `python app.py`

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## DEPLOYMENT (for public URL)

### Option A — Railway (recommended, free tier)
1. Push this folder to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add environment variable: `YOUTUBE_API_KEY=your_key`
4. Railway auto-detects Flask and deploys — you get a public URL

### Option B — Render.com (free tier)
1. Push to GitHub
2. New Web Service → connect repo → Build: `pip install -r requirements.txt`
3. Start: `gunicorn app:app`
4. Add env var `YOUTUBE_API_KEY`

### Option C — PythonAnywhere
1. Upload files → Open Bash console:
   ```bash
   pip install flask requests python-pptx isodate --user
   ```
2. Go to Web tab → Add new web app → Flask → point to `/app/app.py`
3. Set environment variable in WSGI configuration file

---

## FILE STRUCTURE
```
app/
├── app.py               # Flask application (routes)
├── youtube_fetcher.py   # YouTube Data API v3 integration
├── report_generator.py  # PowerPoint report builder (10 slides)
├── requirements.txt
└── templates/
    └── index.html       # Frontend UI
```

## FEATURES
- Accepts 1 company + up to 4 competitors
- Fetches real live YouTube channel & video data
- Displays interactive web report with Chart.js visualisations
- Generates a professional 10-slide PowerPoint (downloadable)
- Scores and ranks all companies on composite metric
- Identifies content gaps and provides actionable recommendations
