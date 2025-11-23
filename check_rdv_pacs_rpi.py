# file: check_rdv_pacs.py
import re, time, random, datetime, sys, subprocess, requests
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

URLS = {
    "MA17": "https://rdvma17.apps.paris.fr/rdvma17/jsp/site/Portal.jsp?page=appointment&view=getViewAppointmentCalendar&id_form=38",
    "MA18": "https://rdvma18.apps.paris.fr/rdvma18/jsp/site/Portal.jsp?page=appointment&view=getViewAppointmentCalendar&id_form=44",
}
CHECK_EVERY_SEC = 60  # ≈ every minute + a little jitter
TIMEOUT = 20

def mac_notify(title, text):
    try:
        subprocess.run(["osascript","-e", f'display notification "{text}" with title "{title}"'],
                        check=False)
    except Exception:
        pass

def extract_events_array(html):
    """
    Extract JS array 'events = [ {...}, {...} ]' and return dicts list (start, end, url, id).
    """
    # 1) isolate the events = [...] block
    m = re.search(r"events\s*=\s*\[(.*?)\];", html, re.S)
    if not m:
        return []
    block = m.group(1)

    # 2) retrieve each object minimally (start, end, id, url)
    #    The site's JS puts lines like:
    #    start : '2026-02-05T09:45', end : '2026-02-05T10:00', id : '153852', url : eventUrl +  '...'
    items = []
    # Normalize newlines and spaces
    block = re.sub(r"\s+", " ", block)
    # Roughly separate objects by '},'
    raw_objs = re.findall(r"\{(.*?)\}", block)
    for ro in raw_objs:
        def pick(field):
            mm = re.search(fr"{field}\s*:\s*'([^']+)'", ro)
            return mm.group(1) if mm else None
        start = pick("start")
        end   = pick("end")
        _id   = pick("id")
        # url can be 'url : eventUrl +  '&id_form=44&starting_date_time=...''
        urlm = re.search(r"url\s*:\s*(?:eventUrl\s*\+\s*)?'([^']+)'", ro)
        url  = urlm.group(1) if urlm else None
        if start and end:
            items.append({"start": start, "end": end, "id": _id, "url_suffix": url})
    return items

def run():
    print("Monitoring PACS slots (17th/18th) – Ctrl+C to stop.")
    seen = set()  # to avoid spamming the notification on the same slots
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            any_found = False
            for label, url in URLS.items():
                r = requests.get(url, timeout=TIMEOUT, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept-Language": "fr-FR,fr;q=0.9",
                })
                r.raise_for_status()
                events = extract_events_array(r.text)
                # If the page contains the "No slot..." banner, events will be [].
                if events:
                    any_found = True
                    fresh = [e for e in events if (label, e["start"], e["end"]) not in seen]
                    if fresh:
                        # Clean log
                        print(f"[{now}] {label}: {len(fresh)} new slot(s) detected.")
                        for e in fresh[:10]:
                            print(f"  • {e['start']} → {e['end']}  (id={e['id']})")
                        mac_notify(f"Appointment {label}", f"{len(fresh)} slot(s) detected. Open the website.")
                        for e in fresh:
                            seen.add((label, e["start"], e["end"]))
                else:
                    print(f"[{now}] {label}: no slot found.")
        except Exception as e:
            print(f"[{now}] Error: {e}", file=sys.stderr)

        # pause ≈ 60 s + slight jitter to stay polite with the server
        time.sleep(max(30, CHECK_EVERY_SEC + random.randint(-5, 8)))

if __name__ == "__main__":
    run()