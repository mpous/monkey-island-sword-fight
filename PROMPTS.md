# Monkey Island Insult Sword Fight - Conversation Log with Claude Code

All the prompts and conversations used to build this project with Claude Code.

---

## Prompt 1: Initial Request

**User:**
> I'm building this app for Arduino UNO Q to run on Arduino App Lab. I want to generate a UI that is the monkey island sword fight with insults. I don't want to use WebUI component as now it's happening, create a flash server with its own UI separated from the bricks. Let me know if you have any questions.

**Claude:**
Created the initial Flask-based architecture:
- `python/main.py` — Flask server with game engine, SSE for real-time updates, keyword_spotting brick integration
- `python/templates/index.html` — Pirate-themed web UI with clickable A/B/C options
- `python/requirements.txt` — Flask dependency
- Updated `app.yaml` — Removed `web_ui` brick, added port 5001, kept `keyword_spotting` brick
- Updated `sketch/sketch.ino` — LED matrix animations for game events via Bridge
- Updated `README.md` — Reflects new Flask architecture

---

## Prompt 2: Flask Not Installed

**User:**
> This is what I see in the logs... ModuleNotFoundError: No module named 'flask'

**Claude:**
Explained that Flask needs to be installed on the UNO Q. The user needed to SSH into the board and run `pip install flask`. App Lab auto-installs dependencies from `requirements.txt` on subsequent launches via its `.cache/.venv` system.

---

## Prompt 3: Callback Signature Error

**User:**
> Now I see these logs... ValueError: Callback must not accept any arguments.

**Claude:**
Fixed the `on_detect` callback signature. The keyword_spotting brick requires callbacks with **no arguments**, but the original code passed a function that accepted a `result` parameter. Fixed by using a closure pattern:

```python
def _make_voice_handler(letter):
    def handler():  # no arguments
        print(f"[MIC] Detected: '{letter}'")
        broadcast("detection", {"label": letter, "time": ts})
        with _game_lock:
            if game.phase == "waiting":
                _handle_answer(letter)
    return handler

for _letter in ("A", "B", "C"):
    _keyword.on_detect(_letter, _make_voice_handler(_letter))
```

---

## Prompt 4: 404 Errors + Inference Visibility

**User:**
> This is what I get in the logs... GET /api/state HTTP/1.1 404... I would like to have more visibility of the inference in the UI. Maybe to add the audio detected through the microphone, a selector to decide where is my USB microphone and select the one I want to use and then see in real-time results of the inferencing. In the other hand use the Edge Impulse logo in the top left and maybe add some images from the Monkey Island game.

**Claude:**
- Added stub routes for `/api/state` and `/api/detection` to avoid 404s from App Lab framework polling
- Added audio device discovery (`arecord -l`) and `/devices` endpoint
- Added Edge Impulse model info retrieval from `http://ei-keyword-spot-runner:1337/api/info` and `/model` endpoint
- Added `on_detect_all` registration for real-time inference confidence bars
- Updated UI with:
  - White brand bar with Edge Impulse logo and app name
  - Audio Device panel with microphone selector and model info display
  - Inference Monitor panel with real-time confidence bars and detection log
  - SSE listeners for `inference` and `detection` named events
  - Monkey Island background image

---

## Prompt 5: UI Refinements - Serial Port & Model Name

**User:**
> The audio device works well but no need for serial port... I would like to see the name of the model. Modify the UI to have the 2 squares 1 next to the other but separate the Audio device part with the Inference Monitor part.

**Claude:**
- Removed the serial port dropdown entirely (was showing "No serial ports found")
- Separated Audio Device and Inference Monitor into two distinct panels in the right column
- Added model name display from Edge Impulse runner API (project name, owner, version, labels)
- Two-panel layout in the right column: Audio Device (top, shrink-to-fit) + Inference Monitor (bottom, fills remaining space)

---

## Prompt 6: Audio Not Working

**User:**
> The app is not getting any audio. So I tested the Hey Arduino! example app and it works well the audio capture inference... [showed Hey Arduino code with `from arduino.app_utils import *`]... Why is the monkey island application not working?

**Claude:**
Identified the **critical missing import**: `from arduino.app_utils import *`. This import provides the `App` and `Bridge` globals. Without it, `App.run()` was never called, so the keyword_spotting brick never started and no audio was captured.

Fixed `main.py`:
```python
_has_app_run = False

try:
    from arduino.app_utils import *  # provides App, Bridge globals
    _has_app_run = True
except ImportError:
    pass

# ... at the end:
if _has_app_run:
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5001, threaded=True, use_reloader=False),
        daemon=True,
    )
    flask_thread.start()
    App.run()  # MUST be called to activate bricks
else:
    app.run(host="0.0.0.0", port=5001, threaded=True)
```

Also fixed Bridge helper to use the global `Bridge.call()` instead of instantiating a new Bridge object.

---

## Prompt 7: Side-by-Side Layout + Larger Fonts + Model Link

**User:**
> I want to have the game-area div and the panel-row div next one to the other. Make the title area and the scoreboard bigger and larger. Font needs to be larger and I don't want to scroll to see everything. Add in the top right of the white menu the link to the A-B-C model with this link https://studio.edgeimpulse.com/public/995535/live

**Claude:**
Complete rewrite of `index.html` with:
- **Two-column CSS Grid layout**: `grid-template-columns: 1fr 380px` filling `calc(100vh - 46px)`
- **Left column**: Title (3.6em Pirata One h1), Scoreboard (3.2em score values), Game area (scrollable parchment, `flex: 1; overflow-y: auto`)
- **Right column**: Audio Device panel (shrink-to-fit) + Inference Monitor panel (`flex: 1`)
- **No scrolling**: `html, body { height: 100%; overflow: hidden; }`
- **A-B-C Model link** in the top-right of the brand bar: `<a class="model-link" href="https://studio.edgeimpulse.com/public/995535/live">A-B-C Model</a>`
- **Responsive**: Stacks vertically below 900px
- Larger fonts throughout: insult text 1.5em, option letters 2em, comeback text 1.15em


