"""
Monkey Island Insult Sword Fight - Flask Edition
=================================================
Standalone Flask server with SSE for real-time game state and inference monitoring.
Uses keyword_spotting brick for voice input on Arduino UNO Q.
Also supports click-based input from the web UI.
"""

import json
import random
import subprocess
import threading
import time
import queue

from flask import Flask, render_template, Response, request, jsonify

# ---------------------------------------------------------------------------
# Optional Arduino UNO Q imports
# ---------------------------------------------------------------------------
_keyword = None
_has_app_run = False

try:
    from arduino.app_utils import *  # noqa: F401,F403 - provides App, Bridge globals
    _has_app_run = True
    print("[INIT] arduino.app_utils loaded (App, Bridge available)")
except ImportError:
    print("[INIT] arduino.app_utils not available (standalone mode)")

try:
    from arduino.app_bricks.keyword_spotting import KeywordSpotting
    _keyword = KeywordSpotting()
    print("[INIT] keyword_spotting brick loaded")
except ImportError:
    print("[INIT] keyword_spotting brick not available")

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# SSE (Server-Sent Events) client management
# ---------------------------------------------------------------------------
_sse_clients = []
_sse_lock = threading.Lock()


def broadcast(event_type, data):
    """Push a named SSE event to all connected clients."""
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _sse_lock:
        dead = []
        for q in _sse_clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)


def broadcast_state():
    broadcast("state", game.get_state())


# ---------------------------------------------------------------------------
# Bridge helper
# ---------------------------------------------------------------------------
def bridge_event(event_name):
    if _has_app_run:
        try:
            Bridge.call(event_name)  # noqa: F821 - provided by app_utils
        except Exception as e:
            print(f"[BRIDGE] {event_name} error: {e}")


# ---------------------------------------------------------------------------
# Insults and comebacks
# ---------------------------------------------------------------------------
ROUNDS = [
    {
        "insult": "Now I know what filth and stupidity really are.",
        "options": {
            "A": "I'm glad to hear you attended your family reunion.",
            "B": "Too bad no one's ever heard of YOU at all.",
            "C": "Your hemorrhoids are flaring up again, eh?"
        },
        "correct": "A"
    },
    {
        "insult": "Every word you say to me is stupid.",
        "options": {
            "A": "Yes there are. You just never learned them.",
            "B": "I wanted to make sure you'd feel comfortable with me.",
            "C": "First you'd better stop waving it like a feather-duster."
        },
        "correct": "B"
    },
    {
        "insult": "I've got a long, sharp lesson for you to learn today.",
        "options": {
            "A": "How appropriate, you fight like a cow!",
            "B": "I'm glad to hear you attended your family reunion.",
            "C": "And I've got a little TIP for you. Get the POINT?"
        },
        "correct": "C"
    },
    {
        "insult": "I will milk every drop of blood from your body!",
        "options": {
            "A": "How appropriate, you fight like a cow!",
            "B": "Even BEFORE they smell your breath?",
            "C": "You run THAT fast?"
        },
        "correct": "A"
    },
    {
        "insult": "I've got the courage and skill of a master swordsman.",
        "options": {
            "A": "He must have taught you everything you know.",
            "B": "Too bad no one's ever heard of YOU at all.",
            "C": "I'd be in real trouble if you ever used them."
        },
        "correct": "C"
    },
    {
        "insult": "My tongue is sharper than any sword.",
        "options": {
            "A": "First you'd better stop waving it like a feather-duster.",
            "B": "I hope now you've learned to stop picking your nose.",
            "C": "You make me think somebody already did."
        },
        "correct": "A"
    },
    {
        "insult": "My name is feared in every dirty corner of this island!",
        "options": {
            "A": "Even BEFORE they smell your breath?",
            "B": "So you got that job as a janitor, after all.",
            "C": "Why, did you want to borrow one?"
        },
        "correct": "B"
    },
    {
        "insult": "My wisest enemies run away at the first sight of me!",
        "options": {
            "A": "Even BEFORE they smell your breath?",
            "B": "I'd be in real trouble if you ever used them.",
            "C": "You run THAT fast?"
        },
        "correct": "A"
    },
    {
        "insult": "Only once have I met such a coward!",
        "options": {
            "A": "Too bad no one's ever heard of YOU at all.",
            "B": "He must have taught you everything you know.",
            "C": "How appropriate, you fight like a cow!"
        },
        "correct": "B"
    },
    {
        "insult": "If your brother's like you, better to marry a pig.",
        "options": {
            "A": "You make me think somebody already did.",
            "B": "I'm glad to hear you attended your family reunion.",
            "C": "Your hemorrhoids are flaring up again, eh?"
        },
        "correct": "A"
    },
    {
        "insult": "No one will ever catch ME fighting as badly as you do.",
        "options": {
            "A": "I hope now you've learned to stop picking your nose.",
            "B": "You run THAT fast?",
            "C": "Why, did you want to borrow one?"
        },
        "correct": "B"
    },
    {
        "insult": "My last fight ended with my hands covered with blood.",
        "options": {
            "A": "I wanted to make sure you'd feel comfortable with me.",
            "B": "So you got that job as a janitor, after all.",
            "C": "I hope now you've learned to stop picking your nose."
        },
        "correct": "C"
    },
    {
        "insult": "I hope you have a boat ready for a quick escape.",
        "options": {
            "A": "Why, did you want to borrow one?",
            "B": "You run THAT fast?",
            "C": "I'd be in real trouble if you ever used them."
        },
        "correct": "A"
    },
    {
        "insult": "My sword is famous all over the Caribbean!",
        "options": {
            "A": "I'm glad to hear you attended your family reunion.",
            "B": "Too bad no one's ever heard of YOU at all.",
            "C": "First you'd better stop waving it like a feather-duster."
        },
        "correct": "B"
    },
    {
        "insult": "You are a pain in the backside, sir!",
        "options": {
            "A": "Your hemorrhoids are flaring up again, eh?",
            "B": "He must have taught you everything you know.",
            "C": "Even BEFORE they smell your breath?"
        },
        "correct": "A"
    },
    {
        "insult": "There are no clever moves that can help you now.",
        "options": {
            "A": "How appropriate, you fight like a cow!",
            "B": "You make me think somebody already did.",
            "C": "Yes there are. You just never learned them."
        },
        "correct": "C"
    },
]


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
_game_lock = threading.Lock()


class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player_score = 0
        self.master_score = 0
        self.current_round_index = 0
        self.phase = "intro"
        self.current_insult = None
        self.fight_log = []
        self.selected_rounds = random.sample(ROUNDS, min(5, len(ROUNDS)))

    def start_fight(self):
        self.phase = "insult"
        self.current_round_index = 0
        self._serve_insult()

    def _serve_insult(self):
        if self.current_round_index < len(self.selected_rounds):
            self.current_insult = self.selected_rounds[self.current_round_index]
            self.phase = "waiting"
        elif self.player_score >= 3:
            self.phase = "win"
        else:
            self.phase = "lose"

    def process_answer(self, choice):
        if self.phase != "waiting" or not self.current_insult:
            return None
        choice = choice.upper()
        if choice not in ("A", "B", "C"):
            return None

        correct_letter = self.current_insult["correct"]
        is_correct = choice == correct_letter

        if is_correct:
            self.player_score += 1
        else:
            self.master_score += 1

        result = {
            "insult": self.current_insult["insult"],
            "chosen": choice,
            "chosen_comeback": self.current_insult["options"][choice],
            "correct_letter": correct_letter,
            "correct_comeback": self.current_insult["options"][correct_letter],
            "is_correct": is_correct,
            "player_score": self.player_score,
            "master_score": self.master_score,
        }
        self.fight_log.append(result)

        if self.player_score >= 3:
            self.phase = "win"
        elif self.master_score >= 3:
            self.phase = "lose"
        else:
            self.phase = "result"

        return result

    def next_round(self):
        if self.phase == "result":
            self.current_round_index += 1
            self._serve_insult()

    def get_state(self):
        state = {
            "phase": self.phase,
            "player_score": self.player_score,
            "master_score": self.master_score,
            "round": self.current_round_index + 1,
            "total_rounds": len(self.selected_rounds),
            "fight_log": self.fight_log,
        }
        if self.phase == "waiting" and self.current_insult:
            state["insult"] = self.current_insult["insult"]
            state["options"] = self.current_insult["options"]
        if self.phase == "result" and self.fight_log:
            state["last_result"] = self.fight_log[-1]
        return state


game = GameState()


# ---------------------------------------------------------------------------
# Shared answer processing (used by both click and voice)
# ---------------------------------------------------------------------------
def _handle_answer(choice):
    """Process an answer and broadcast the result. Must be called with _game_lock held."""
    result = game.process_answer(choice)
    if not result:
        return None

    if result["is_correct"]:
        print(f"[GAME] CORRECT! '{result['chosen_comeback']}'")
        bridge_event("CORRECT")
    else:
        print(f"[GAME] WRONG! Was {result['correct_letter']}: '{result['correct_comeback']}'")
        bridge_event("WRONG")

    broadcast_state()

    if game.phase == "result":
        threading.Timer(3.0, _advance_round).start()
    elif game.phase == "win":
        print("[GAME] === YOU WIN! ===")
        bridge_event("WIN")
    elif game.phase == "lose":
        print("[GAME] === YOU LOSE! ===")
        bridge_event("LOSE")

    return result


def _advance_round():
    with _game_lock:
        game.next_round()
        broadcast_state()
        if game.phase == "waiting" and game.current_insult:
            print(f"[GAME] Sword Master says: '{game.current_insult['insult']}'")


# ---------------------------------------------------------------------------
# Audio device discovery & model info
# ---------------------------------------------------------------------------
def _list_audio_devices():
    """List available audio input devices (ALSA)."""
    devices = []
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            if line.startswith("card"):
                devices.append(line.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return devices if devices else ["No audio devices detected"]


def _get_model_info():
    """Try to get the EI model name from the keyword spotting runner."""
    import urllib.request
    try:
        req = urllib.request.urlopen("http://ei-keyword-spot-runner:1337/api/info", timeout=3)
        data = json.loads(req.read())
        project = data.get("project", {})
        model = data.get("model_parameters", {})
        return {
            "name": project.get("name", "Unknown"),
            "owner": project.get("owner", ""),
            "version": project.get("deploy_version", ""),
            "labels": model.get("labels", []),
            "sensor": model.get("sensor", ""),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/state")
def get_state():
    with _game_lock:
        return jsonify(game.get_state())


@app.route("/events")
def events():
    q = queue.Queue(maxsize=100)
    with _sse_lock:
        _sse_clients.append(q)

    def stream():
        try:
            with _game_lock:
                initial = json.dumps(game.get_state())
            yield f"event: state\ndata: {initial}\n\n"
            while True:
                data = q.get()
                yield data
        except GeneratorExit:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/action", methods=["POST"])
def action():
    body = request.json or {}
    act = body.get("action", "")

    with _game_lock:
        if act in ("start", "restart"):
            game.reset()
            game.start_fight()
            bridge_event("START")
            broadcast_state()
            if game.current_insult:
                print("[GAME] === FIGHT STARTED! ===")
                print(f"[GAME] Sword Master says: '{game.current_insult['insult']}'")
            return jsonify({"ok": True})

        if act == "answer":
            choice = body.get("choice", "").upper()
            result = _handle_answer(choice)
            return jsonify({"ok": result is not None})

    return jsonify({"ok": False})


@app.route("/devices")
def devices():
    return jsonify({"audio": _list_audio_devices()})


@app.route("/model")
def model():
    info = _get_model_info()
    if info:
        return jsonify(info)
    return jsonify({"name": "Not available", "labels": [], "sensor": "", "owner": "", "version": ""})


# Stub routes for App Lab framework polling (avoids 404s in logs)
@app.route("/api/state")
def api_state():
    with _game_lock:
        return jsonify(game.get_state())


@app.route("/api/detection")
def api_detection():
    return jsonify({"detections": []})


# ---------------------------------------------------------------------------
# Keyword spotting callbacks (voice input on UNO Q)
# ---------------------------------------------------------------------------
_last_inference_time = 0


def _make_voice_handler(letter):
    """on_detect(keyword, callback) — callback takes no arguments."""
    def handler():
        print(f"[MIC] Detected: '{letter}'")
        ts = time.strftime("%H:%M:%S")
        broadcast("detection", {"label": letter, "time": ts})
        with _game_lock:
            if game.phase == "waiting":
                print(f"[GAME] Voice chose: {letter}")
                _handle_answer(letter)
    return handler


def _handle_all_detections(detections):
    """on_detect_all callback — receives dict {label: confidence}. Throttled to ~3/sec."""
    global _last_inference_time
    now = time.time()
    if now - _last_inference_time < 0.3:
        return
    _last_inference_time = now
    broadcast("inference", detections)


if _keyword:
    for _letter in ("A", "B", "C"):
        _keyword.on_detect(_letter, _make_voice_handler(_letter))



# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------
print("=" * 60)
print("  MONKEY ISLAND INSULT SWORD FIGHT")
print("  Open http://<device-ip>:5001 to play!")
print("  Say A, B, or C into the microphone (on UNO Q)")
print("  Or click the options in the browser")
print("=" * 60)

if _has_app_run:
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5001, threaded=True, use_reloader=False),
        daemon=True,
    )
    flask_thread.start()
    App.run()  # noqa: F821
else:
    app.run(host="0.0.0.0", port=5001, threaded=True)
