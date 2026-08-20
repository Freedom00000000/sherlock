#!/usr/bin/env python3
"""
Sherlock OSINT Dashboard — combined username search + deep OSINT gathering.
Run: python app.py  (opens browser at http://localhost:5000)
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from queue import Empty, Queue

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

app = Flask(__name__, template_folder="templates", static_folder="static")

# ─── persistent per-search state ────────────────────────────────────────────

class SearchJob:
    def __init__(self, search_id: str):
        self.id = search_id
        self.queue: Queue = Queue()
        self.results: list[dict] = []
        self.done = False
        self.proc: subprocess.Popen | None = None

_jobs: dict[str, SearchJob] = {}
_jobs_lock = threading.Lock()

def _get_job(sid: str) -> SearchJob | None:
    with _jobs_lock:
        return _jobs.get(sid)

def _new_job(sid: str) -> SearchJob:
    job = SearchJob(sid)
    with _jobs_lock:
        _jobs[sid] = job
    return job

# ─── cheater / dating site list ─────────────────────────────────────────────

CHEATER_SITES = [
    "DanishDatingNet", "DenmarkPassions", "Nydate", "datingRU",
    "APClips", "AdmireMe.Vip", "BongaCams", "ChaturBate", "Erome",
    "Image Fap", "LushStories", "Motherless", "PocketStars", "Pornhub",
    "RedTube", "RocketTube", "TnAFlix", "Xvideos", "YouPorn", "xHamster",
    "Instagram", "Snapchat", "TikTok", "Twitter", "Telegram",
    "Reddit", "Discord", "Kik", "Flickr",
]

# ─── deep OSINT checks (SpiderFoot-style) ───────────────────────────────────

def _check_email_breach(email: str) -> dict:
    """Check Have I Been Pwned (public v3 API, no key for count)."""
    import urllib.request, urllib.error
    result = {"source": "HaveIBeenPwned", "found": False, "detail": ""}
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Sherlock-OSINT-Dashboard/1.0",
            "hibp-api-key": ""  # public lookup — returns 401 without key; we catch that
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            names = [d["Name"] for d in data]
            result["found"] = True
            result["detail"] = f"Found in {len(names)} breach(es): {', '.join(names[:5])}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            result["detail"] = "Not found in any known breach"
        elif e.code == 401:
            result["detail"] = "API key required for breach lookup — visit haveibeenpwned.com"
        else:
            result["detail"] = f"HTTP {e.code}"
    except Exception as ex:
        result["detail"] = f"Error: {ex}"
    return result


def _check_username_gravatar(username: str) -> dict:
    """Check if a Gravatar profile exists for this username as an email hash hint."""
    import hashlib, urllib.request, urllib.error
    result = {"source": "Gravatar", "found": False, "detail": "", "url": ""}
    try:
        # Gravatar uses MD5 of lowercase email; we try username@gmail.com as a heuristic
        email_guess = f"{username}@gmail.com"
        h = hashlib.md5(email_guess.lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/{h}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Sherlock-OSINT/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            entry = data.get("entry", [{}])[0]
            display = entry.get("displayName", username)
            result["found"] = True
            result["url"] = f"https://gravatar.com/{h}"
            result["detail"] = f"Gravatar profile found: {display}"
    except Exception:
        result["detail"] = "No Gravatar profile found"
    return result


def _check_github_user(username: str) -> dict:
    """Fetch basic GitHub profile info."""
    import urllib.request, urllib.error
    result = {"source": "GitHub API", "found": False, "detail": "", "url": ""}
    try:
        url = f"https://api.github.com/users/{username}"
        req = urllib.request.Request(url, headers={"User-Agent": "Sherlock-OSINT/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            result["found"] = True
            result["url"] = data.get("html_url", "")
            bio = data.get("bio") or ""
            repos = data.get("public_repos", 0)
            followers = data.get("followers", 0)
            result["detail"] = (
                f"GitHub: {data.get('name', username)} | "
                f"{repos} repos | {followers} followers"
                + (f" | Bio: {bio[:80]}" if bio else "")
            )
    except Exception:
        result["detail"] = "No GitHub account found"
    return result


def _dns_lookup(domain: str) -> dict:
    """Resolve domain to IPs."""
    import socket
    result = {"source": "DNS", "found": False, "detail": ""}
    try:
        ips = socket.getaddrinfo(domain, None)
        unique = sorted({r[4][0] for r in ips})
        result["found"] = bool(unique)
        result["detail"] = "IPs: " + ", ".join(unique[:6])
    except Exception as ex:
        result["detail"] = f"DNS error: {ex}"
    return result


def _whois_lookup(domain: str) -> dict:
    """Simple WHOIS via rdap.org."""
    import urllib.request
    result = {"source": "WHOIS/RDAP", "found": False, "detail": "", "url": ""}
    try:
        url = f"https://rdap.org/domain/{domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "Sherlock-OSINT/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result["found"] = True
        result["url"] = url
        # extract registrar
        entities = data.get("entities", [])
        registrar = next(
            (e.get("vcardArray", [[]])[1] for e in entities
             if "registrar" in e.get("roles", [])), None
        )
        reg_name = ""
        if registrar:
            for card in registrar:
                if card[0] == "fn":
                    reg_name = card[3]
                    break
        events = {e["eventAction"]: e["eventDate"] for e in data.get("events", [])}
        reg_date = events.get("registration", "unknown")[:10]
        result["detail"] = f"Registered: {reg_date}" + (f" | Registrar: {reg_name}" if reg_name else "")
    except Exception as ex:
        result["detail"] = f"RDAP error: {ex}"
    return result


# ─── Sherlock subprocess runner ──────────────────────────────────────────────

def _run_sherlock(job: SearchJob, username: str, mode: str, nsfw: bool, sites: list[str]):
    """Run Sherlock in a subprocess and stream results into job.queue."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "sherlock_project", "resources", "data.json")
    cmd = [
        sys.executable, "-m", "sherlock_project",
        "--print-found",
        "--no-color",
        "--local",
        "--data-file", os.path.abspath(data_path),
    ]
    if nsfw:
        cmd.append("--nsfw")
    if mode == "cheater":
        for s in CHEATER_SITES:
            cmd += ["--site", s]
    elif sites:
        for s in sites:
            cmd += ["--site", s]
    cmd.append(username)

    try:
        job.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in job.proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            # parse "[+] SiteName: https://..." lines
            m = re.match(r"\[\+\]\s+(.+?):\s+(https?://\S+)", line)
            if m:
                entry = {"site": m.group(1), "url": m.group(2), "status": "found"}
                job.results.append(entry)
                job.queue.put({"type": "result", "data": entry})
            else:
                job.queue.put({"type": "log", "text": line})
        job.proc.wait()
    except Exception as ex:
        job.queue.put({"type": "log", "text": f"Error running Sherlock: {ex}"})
    finally:
        job.done = True
        job.queue.put({"type": "done"})


# ─── Flask routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    mode = body.get("mode", "all")          # all | cheater | custom
    nsfw = bool(body.get("nsfw", False))
    sites = body.get("sites", [])

    if not username:
        return jsonify({"error": "username required"}), 400

    sid = f"{username}-{mode}-{int(time.time()*1000)}"
    job = _new_job(sid)

    t = threading.Thread(
        target=_run_sherlock,
        args=(job, username, mode, nsfw, sites),
        daemon=True,
    )
    t.start()
    return jsonify({"search_id": sid})


@app.route("/api/stream/<sid>")
def api_stream(sid: str):
    """Server-Sent Events stream for live results."""
    job = _get_job(sid)
    if not job:
        return jsonify({"error": "unknown search_id"}), 404

    def event_gen():
        while True:
            try:
                msg = job.queue.get(timeout=30)
            except Empty:
                yield "event: ping\ndata: {}\n\n"
                if job.done:
                    break
                continue
            yield f"data: {json.dumps(msg)}\n\n"
            if msg.get("type") == "done":
                break

    return Response(event_gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/stop/<sid>", methods=["POST"])
def api_stop(sid: str):
    job = _get_job(sid)
    if job and job.proc:
        job.proc.terminate()
        job.done = True
        job.queue.put({"type": "done"})
    return jsonify({"ok": True})


@app.route("/api/deep", methods=["POST"])
def api_deep():
    """Run SpiderFoot-style deep OSINT checks."""
    body = request.get_json(force=True)
    target = (body.get("target") or "").strip()
    kind = body.get("kind", "username")   # username | email | domain

    if not target:
        return jsonify({"error": "target required"}), 400

    checks = []
    if kind == "username":
        checks.append(_check_github_user(target))
        checks.append(_check_username_gravatar(target))
    elif kind == "email":
        checks.append(_check_email_breach(target))
        checks.append(_check_username_gravatar(target.split("@")[0]))
        if "@" in target:
            domain = target.split("@", 1)[1]
            checks.append(_dns_lookup(domain))
            checks.append(_whois_lookup(domain))
    elif kind == "domain":
        checks.append(_dns_lookup(target))
        checks.append(_whois_lookup(target))

    return jsonify({"results": checks})


@app.route("/api/export/<sid>", methods=["GET"])
def api_export(sid: str):
    """Export results as CSV."""
    job = _get_job(sid)
    if not job:
        return jsonify({"error": "unknown search_id"}), 404
    fmt = request.args.get("fmt", "csv")
    if fmt == "csv":
        lines = ["Site,URL"]
        for r in job.results:
            lines.append(f"{r['site']},{r['url']}")
        return Response("\n".join(lines), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=sherlock_{sid}.csv"})
    else:
        text = "\n".join(f"[+] {r['site']}: {r['url']}" for r in job.results)
        return Response(text, mimetype="text/plain",
                        headers={"Content-Disposition": f"attachment; filename=sherlock_{sid}.txt"})


if __name__ == "__main__":
    import webbrowser
    print("Starting Sherlock OSINT Dashboard on http://localhost:5000")
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
