import os, json, threading, io

# Load .env file if present (always overwrites, .env takes priority)
try:
    with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()
except FileNotFoundError:
    pass

from flask import Flask, render_template, request, jsonify, send_file
from youtube_fetcher import fetch_company_data, add_fmt
from report_generator import generate_pptx, _rank_companies

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET","mypromovideos-r2-secret")

# Log API key status on startup (no key value shown)
api_key = os.environ.get("YOUTUBE_API_KEY","")
print(f"[STARTUP] YOUTUBE_API_KEY {'SET (' + str(len(api_key)) + ' chars)' if api_key else 'NOT SET'}")

# In-memory job store
jobs = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    your_company = (data.get("your_company") or "").strip()
    competitors  = [c.strip() for c in data.get("competitors",[]) if c.strip()]
    if not your_company:
        return jsonify({"error":"Please enter your company name."}), 400
    all_names = [your_company] + competitors[:4]
    job_id = f"job_{len(jobs)+1}"
    jobs[job_id] = {"status":"running","progress":0,"results":[],"error":None}

    def run():
        try:
            results = []
            for i, name in enumerate(all_names):
                jobs[job_id]["progress"] = int((i/len(all_names))*90)
                try:
                    d = fetch_company_data(name)
                    d = add_fmt(d)
                except Exception as e:
                    d = {"company_name": name, "channel_id": None, "channel_title": None,
                         "channel_description": "", "channel_url": None, "channel_thumbnail": None,
                         "subscriber_count": 0, "video_count": 0, "view_count": 0,
                         "country": "N/A", "created_at": "N/A", "videos": [], "top_videos": [],
                         "avg_views": 0, "avg_likes": 0, "avg_comments": 0,
                         "upload_freq_per_week": 0, "topics": [], "score": 0,
                         "subscriber_count_fmt": "0", "video_count_fmt": "0",
                         "view_count_fmt": "0", "avg_views_fmt": "0",
                         "avg_likes_fmt": "0", "avg_comments_fmt": "0",
                         "error": f"Error fetching data: {str(e)}"}
                results.append(d)
            scores = _rank_companies(results)
            for r in results:
                r["score"] = scores.get(r["company_name"], 0)
            jobs[job_id]["results"] = results
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["your_company"] = your_company
        except Exception as e:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["your_company"] = your_company
            jobs[job_id]["results"] = [{"company_name": n, "error": str(e),
                "channel_id":None,"channel_title":None,"subscriber_count":0,
                "video_count":0,"view_count":0,"avg_views":0,"avg_likes":0,
                "avg_comments":0,"upload_freq_per_week":0,"topics":[],"videos":[],
                "top_videos":[],"score":0,"subscriber_count_fmt":"0",
                "video_count_fmt":"0","view_count_fmt":"0","avg_views_fmt":"0",
                "avg_likes_fmt":"0","avg_comments_fmt":"0"} for n in all_names]

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error":"Job not found"}), 404
    return jsonify({
        "status":   job["status"],
        "progress": job["progress"],
        "error":    job.get("error"),
        "results":  job.get("results",[]) if job["status"]=="done" else [],
        "your_company": job.get("your_company",""),
    })

@app.route("/download/<job_id>")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return "Report not ready", 400
    all_data     = job["results"]
    your_company = job.get("your_company","Your Company")
    pptx_bytes   = generate_pptx(all_data, your_company)
    return send_file(
        io.BytesIO(pptx_bytes),
        as_attachment=True,
        download_name="Video_Competitor_Intelligence_Report.pptx",
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5000)
