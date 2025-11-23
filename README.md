# find-pacs-date

Two small helper scripts to monitor Paris PACS appointment slots and view the logs.

These scripts were made in **vibecoding**.

> Note: In France, *PACS* ("Pacte civil de solidarité") is a form of civil union. This script was originally written to monitor PACS appointment slots at the 17th district city hall (MA17). The 18th district (MA18) endpoint was added mainly for testing purposes, because its calendar had more frequent changes and was therefore convenient to validate the logic. Keeping MA18 is purely optional; the tool works fine with only MA17 (or any single city hall) configured. You may also enter the URL of the Paris town hall of your choice.

## Files

- `check_rdv_pacs_rpi.py`  
  Periodically checks the Paris PACS appointment pages (MA17 / MA18), looks for new available slots and prints them to stdout. On macOS it can also trigger desktop notifications.

- `log-viewer.py`  
  Very small Flask web app that serves the PACS monitoring log file in a browser (last lines, live streaming view, and download).

## Requirements

- Python 3
- On Raspberry Pi: a basic Python 3 install is enough
- tmux is an advice
- For `log-viewer.py` you need Flask:
  - `pip install flask`

The log viewer reads from a file whose path is defined by the `PACS_LOG_PATH` environment variable, e.g. `/home/pi/pacs.log`. If not set, it uses a default path hard‑coded in the script.

## Typical Raspberry Pi setup (with tmux)

You can run everything in two `tmux` sessions so it keeps running in the background.

### 1. Start the PACS checker (session 1)

1. Connect to the Raspberry Pi (SSH).  
2. Create / attach a tmux session, e.g. `tmux new -s pacs-checker`.  
3. In that session, run:
   - `python3 check_rdv_pacs_rpi.py | tee -a /home/pi/pacs.log`

This will:
- Continuously check for slots every ~60 seconds (with a small jitter).
- Append all output to `/home/pi/pacs.log`.

Detach from tmux with `Ctrl+b` then `d`.

### 2. Start the log viewer (session 2)

1. Create another tmux session, e.g. `tmux new -s pacs-viewer`.  
2. Ensure the `PACS_LOG_PATH` environment variable points to your log file, for example:
   - `export PACS_LOG_PATH=/home/pi/pacs.log`
3. Start the web viewer:
   - `python3 log-viewer.py`

By default it listens on port 8080 on all interfaces (`0.0.0.0`). From your computer (on the same network or via VPN/SSH tunnel), open:

- `http://<ip_of_your_pi>:8080/`

You will see:
- Last lines of the log (auto-refresh every 10s)
- A **Download** link to get the full log file
- A **Live** view that auto-scrolls like `tail -f`

## Notes

- The scripts are lightweight and intended to be hacked/adjusted quickly (URLs, log path, etc.).
- Be reasonable with the polling interval to avoid overloading the remote site.
