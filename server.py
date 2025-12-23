import json
import queue
import threading
from flask import Flask, request, jsonify
import tkinter as tk
import os

# ===========================
# Globals
# ===========================
reset_timer = None
RESET_DELAY = 10  # seconds

# ===========================
# Referee Registry
# ===========================
class RefereeRegistry:
    def __init__(self):
        self.lock = threading.Lock()
        self.assigned = {
            "left": False,
            "center": False,
            "right": False,
        }

    def register(self, referee):
        with self.lock:
            if referee not in self.assigned:
                return False, "Invalid referee"

            if self.assigned[referee]:
                return False, "Position already taken"

            self.assigned[referee] = True
            return True, "Registered"

    def reset(self):
        with self.lock:
            for k in self.assigned:
                self.assigned[k] = False

referees = RefereeRegistry()

# ===========================
# Vote Buffer
# ===========================
class VoteBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.votes = {
            "left": None,
            "center": None,
            "right": None,
        }

    def submit_vote(self, referee, color):
        with self.lock:
            if referee not in self.votes:
                return False
            self.votes[referee] = color
            return True

    def all_votes_in(self):
        with self.lock:
            return all(v is not None for v in self.votes.values())

    def snapshot(self):
        with self.lock:
            return dict(self.votes)

    def clear(self):
        with self.lock:
            for k in self.votes:
                self.votes[k] = None

vote_buffer = VoteBuffer()

# ===========================
# Flask Server
# ===========================
app = Flask(__name__)
color_queue = queue.Queue()

@app.route("/button", methods=["POST"])
def button():
    try:
        data = request.get_json(force=True)
        print(data)

        referee = data.get("referee", "").lower()
        action = data.get("action")

        if action == "register":
            ok, msg = referees.register(referee)
            return jsonify({"ok": ok, "message": msg if not ok else "Registered"}), (200 if ok else 409)

        elif action == "vote":
            color = data.get("button", "").lower()
            if color not in ("red", "white"):
                return jsonify({"error": "Invalid color"}), 400

            ok = vote_buffer.submit_vote(referee, color)
            if not ok:
                return jsonify({"error": "Invalid referee"}), 400

            # ✅ Only display lights if all 3 votes are in
            if vote_buffer.all_votes_in():
                votes = vote_buffer.snapshot()
                for ref, col in votes.items():
                    color_queue.put((ref, col))

                # Schedule lights reset after 10 seconds
                schedule_light_reset()

                # Clear vote buffer for next attempt AFTER lights are drawn
                vote_buffer.clear()

            return jsonify({"ok": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ===========================
# Light Reset Logic
# ===========================
def schedule_light_reset():
    global reset_timer

    if reset_timer is not None:
        reset_timer.cancel()

    def do_reset():
        color_queue.put(("reset", None))

    reset_timer = threading.Timer(RESET_DELAY, do_reset)
    reset_timer.daemon = True
    reset_timer.start()

@app.route("/reset", methods=["POST"])
def reset():
    referees.reset()
    vote_buffer.clear()

    # clear pending queue items
    while not color_queue.empty():
        color_queue.get()

    # reset lights visually
    color_queue.put(("left", "grey20"))
    color_queue.put(("center", "grey20"))
    color_queue.put(("right", "grey20"))

    return jsonify({"ok": True, "message": "Election reset"}), 200

# ===========================
# Flask Runner
# ===========================
def run_flask():
    cert_file = r"C:\Users\netadmin\Documents\Cursor_Projects\bar_load_assistent\lights_app\crypto\lights_app.crt"
    key_file  = r"C:\Users\netadmin\Documents\Cursor_Projects\bar_load_assistent\lights_app\crypto\lights_app.key"

    app.run(
        host="0.0.0.0",
        port=443,
        debug=False,
        use_reloader=False,
        ssl_context=(cert_file, key_file)
    )

# ===========================
# Tkinter UI
# ===========================
class LightUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Powerlifting Lights")
        self.root.attributes("-fullscreen", True)

        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.circles = []
        self.default_color = "grey20"
        self.referee_to_index = {"left": 0, "center": 1, "right": 2}

        self.root.after_idle(self.draw_circles)
        self.canvas.bind("<Configure>", lambda e: self.redraw_circles())
        self.check_queue()

    def draw_circles(self):
        self.canvas.update_idletasks()
        self.circles.clear()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        radius = min(width // 6, height // 3)
        spacing = radius * 2 + 40
        center_y = height // 2
        start_x = (width - (spacing * 2)) // 2

        for i in range(3):
            x = start_x + i * spacing
            circle = self.canvas.create_oval(
                x - radius, center_y - radius,
                x + radius, center_y + radius,
                fill=self.default_color,
                outline="grey50",
                width=4
            )
            self.circles.append(circle)

    def redraw_circles(self):
        self.canvas.delete("all")
        self.draw_circles()

    def check_queue(self):
        while not color_queue.empty():
            item = color_queue.get()
            if item[0] == "reset":
                for c in self.circles:
                    self.canvas.itemconfig(c, fill=self.default_color)
                continue

            referee, color = item
            index = self.referee_to_index.get(referee)
            if index is not None:
                self.canvas.itemconfig(self.circles[index], fill=color)

        self.root.after(100, self.check_queue)

# ===========================
# Main
# ===========================
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    root = tk.Tk()
    app_ui = LightUI(root)
    root.mainloop()
