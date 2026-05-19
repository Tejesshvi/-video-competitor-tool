import os, re, requests, isodate
from datetime import datetime, timezone
from collections import Counter

API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyAFIGk-ALF8zMVgPBDvJJVcNWJF-mFjZ_g")
BASE = "https://www.googleapis.com/youtube/v3"

def _get(endpoint, params):
    params["key"] = API_KEY
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def _fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def _dur(s):
    try: return int(isodate.parse_duration(s).total_seconds())
    except: return 0

def search_channel(name):
    d = _get("search", {"part":"snippet","q":name,"type":"channel","maxResults":5})
    items = d.get("items", [])
    if not items: return None
    nl = name.lower()
    for it in items:
        t = it["snippet"]["channelTitle"].lower()
        if nl in t or t in nl: return it
    return items[0]

def get_channel_details(cid):
    d = _get("channels", {"part":"snippet,statistics,contentDetails","id":cid})
    items = d.get("items", [])
    return items[0] if items else {}

def get_videos(playlist_id, max_results=50):
    videos, token = [], None
    while len(videos) < max_results:
        p = {"part":"snippet","playlistId":playlist_id,"maxResults":min(50,max_results-len(videos))}
        if token: p["pageToken"] = token
        d = _get("playlistItems", p)
        videos.extend(d.get("items",[]))
        token = d.get("nextPageToken")
        if not token: break
    return videos

def get_stats(vids):
    if not vids: return {}
    d = _get("videos", {"part":"statistics,contentDetails,snippet","id":",".join(vids[:50])})
    return {it["id"]: it for it in d.get("items",[])}

STOP = {"the","a","an","is","in","on","at","for","to","of","and","or","with","how","why",
        "what","this","that","are","you","your","we","i","it","its","be","by","from","as",
        "was","were","has","have","do","does","did","my","our","will","can","just","all",
        "but","not","more","about","they","their","its","video"}

def fetch_company_data(company_name, max_videos=50):
    res = {"company_name":company_name,"channel_id":None,"channel_title":None,
           "channel_description":"","channel_url":None,"channel_thumbnail":None,
           "subscriber_count":0,"video_count":0,"view_count":0,"country":"N/A",
           "created_at":"N/A","videos":[],"top_videos":[],"avg_views":0,"avg_likes":0,
           "avg_comments":0,"upload_freq_per_week":0,"topics":[],"error":None}
    try:
        si = search_channel(company_name)
        if not si: res["error"] = f"No channel found for '{company_name}'"; return res
        cid = si["snippet"]["channelId"]
        ch = get_channel_details(cid)
        if not ch: res["error"] = "Channel details not found"; return res
        snip = ch.get("snippet",{}); stats = ch.get("statistics",{})
        cd = ch.get("contentDetails",{})
        res.update({
            "channel_id": cid,
            "channel_title": snip.get("title", company_name),
            "channel_description": snip.get("description",""),
            "channel_url": f"https://www.youtube.com/channel/{cid}",
            "channel_thumbnail": snip.get("thumbnails",{}).get("default",{}).get("url",""),
            "subscriber_count": int(stats.get("subscriberCount",0)),
            "video_count": int(stats.get("videoCount",0)),
            "view_count": int(stats.get("viewCount",0)),
            "country": snip.get("country","N/A"),
            "created_at": snip.get("publishedAt","N/A")[:10],
        })
        pl_id = cd.get("relatedPlaylists",{}).get("uploads")
        if not pl_id: return res
        items = get_videos(pl_id, max_videos)
        vids = [it["snippet"]["resourceId"]["videoId"] for it in items if it.get("snippet",{}).get("resourceId",{}).get("videoId")]
        vstats = get_stats(vids[:50])
        evids, words = [], []
        for it in items:
            vid = it.get("snippet",{}).get("resourceId",{}).get("videoId")
            if not vid: continue
            si2 = vstats.get(vid, {}); st = si2.get("statistics",{}); snip2 = si2.get("snippet", it.get("snippet",{}))
            views=int(st.get("viewCount",0)); likes=int(st.get("likeCount",0)); comments=int(st.get("commentCount",0))
            title = snip2.get("title",""); pub = snip2.get("publishedAt","")[:10]
            thumb = snip2.get("thumbnails",{}).get("medium",{}).get("url","") or snip2.get("thumbnails",{}).get("default",{}).get("url","")
            eng = round((likes+comments)/views*100,2) if views else 0
            evids.append({"id":vid,"title":title,"published":pub,"views":views,"likes":likes,
                          "comments":comments,"engagement_rate":eng,"url":f"https://www.youtube.com/watch?v={vid}","thumbnail":thumb})
            ws = re.sub(r"[^a-zA-Z\s]","",title.lower()).split()
            words.extend([w for w in ws if w not in STOP and len(w)>3])
        if evids:
            evids.sort(key=lambda v:v["views"],reverse=True)
            res["videos"]=evids; res["top_videos"]=evids[:5]
            res["avg_views"]=round(sum(v["views"] for v in evids)/len(evids))
            res["avg_likes"]=round(sum(v["likes"] for v in evids)/len(evids))
            res["avg_comments"]=round(sum(v["comments"] for v in evids)/len(evids))
            try:
                dt=datetime.fromisoformat(snip.get("publishedAt","").rstrip("Z")).replace(tzinfo=timezone.utc)
                weeks=max(1,(datetime.now(timezone.utc)-dt).days/7)
                res["upload_freq_per_week"]=round(len(evids)/weeks,2)
            except: pass
            res["topics"]=[w for w,_ in Counter(words).most_common(10)]
    except requests.exceptions.HTTPError as e:
        res["error"]=f"API error {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        res["error"]=f"Error: {str(e)}"
    return res

def add_fmt(d):
    for k in ["subscriber_count","video_count","view_count","avg_views","avg_likes","avg_comments"]:
        d[f"{k}_fmt"] = _fmt(d[k])
    return d
