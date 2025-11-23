from flask import Flask, Response, request, abort
import os
from datetime import datetime

LOG_PATH = os.environ.get("PACS_LOG_PATH", "/home/pi/dev/pacs.log")
TITLE = "PACS Monitoring Logs"

app = Flask(__name__)

HTML_TPL = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:system-ui,Arial,sans-serif;max-width:900px;margin:24px auto;padding:0 12px;background:#fafafa;color:#222}}
h1{{font-size:20px;margin:0 0 10px}}
small{{color:#666}}
pre{{background:#111;color:#eee;padding:12px;border-radius:6px;white-space:pre-wrap;word-wrap:break-word}}
a.button{{display:inline-block;margin:8px 8px 0 0;padding:6px 10px;border:1px solid #ccc;border-radius:4px;text-decoration:none;color:#222;background:#fff}}
</style>
<meta http-equiv="refresh" content="{refresh}">
</head><body>
<h1>{title}</h1>
<small>Server time: {now}</small><br>
<a class="button" href="/">Last lines</a>
<a class="button" href="/download">Download</a>
<a class="button" href="/stream">Live (auto-scroll)</a>
<pre>{content}</pre>
</body></html>"""

def tail_lines(path, n=1500):
    if not os.path.exists(path):
        return []
    # Efficient reading without loading the whole file
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 1024
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                f.seek(size - step)
                data = f.read(step) + data
                size -= step
            lines = data.splitlines()[-n:]
            return [ln.decode("utf-8", "ignore") for ln in lines]
    except Exception as e:
        return [f"[viewer] Read error: {e}"]

@app.route("/")
def home():
    lines = tail_lines(LOG_PATH, n=300)
    html = HTML_TPL.format(
        title=TITLE,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        content="\n".join(lines) if lines else "(no logs yet)",
        refresh=10,  # auto-refresh 10 s
    )
    return Response(html, mimetype="text/html")

@app.route("/download")
def download():
    if not os.path.exists(LOG_PATH):
        return "No logs found."
    with open(LOG_PATH, "rb") as f:
        data = f.read()
    return Response(data, headers={
        "Content-Disposition": "attachment; filename=pacs.log"
    }, mimetype="text/plain")

@app.route("/stream")
def stream():
    """
    Simple "live" stream (refreshes every 2s on client side).
    """
    return Response(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Live</title>
<style>body{{margin:0}} pre{{margin:0;padding:12px;background:#111;color:#eee;height:100vh;overflow:auto;}}</style>
</head>
<body>
<pre id="log"></pre>
<script>
async function fetchLog(){{
  const r = await fetch('/tail');
  const t = await r.text();
  const pre = document.getElementById('log');
  const atBottom = (pre.scrollTop + pre.clientHeight) >= (pre.scrollHeight - 5);
  pre.textContent = t;
  if(atBottom) pre.scrollTop = pre.scrollHeight;
}}
setInterval(fetchLog, 2000);
fetchLog();
</script>
</body></html>""", mimetype="text/html")

@app.route("/tail")
def tail_plain():
    lines = tail_lines(LOG_PATH, n=500)
    return Response("\n".join(lines), mimetype="text/plain")

if __name__ == "__main__":
    # listen on all interfaces to access via VPN
    app.run(host="0.0.0.0", port=8080)
