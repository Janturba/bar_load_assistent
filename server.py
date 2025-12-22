import json
import queue
import threading
from turtle import color
from flask import Flask, request, jsonify
import tkinter as tk
import os

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

referees = RefereeRegistry()

# ===========================
# Flask server in separate thread
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
            if not ok:
                return jsonify({"ok": False, "message": msg}), 400

            return jsonify({"ok": True}), 200

        elif action == "vote":
            color = data.get("button", "").lower()
            if color not in ("red", "white"):
                return jsonify({"error": "Invalid color"}), 400

            color_queue.put((referee, color))
            return jsonify({"ok": True}), 200

        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400


def run_flask():
    # Path to your self-signed cert and key
    cert_file = r"C:\Users\netadmin\Documents\Cursor_Projects\bar_load_assistent\lights_app\crypto\lights_app.crt"
    key_file  = r"C:\Users\netadmin\Documents\Cursor_Projects\bar_load_assistent\lights_app\crypto\lights_app.key"


    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("SSL certificate or key not found! Run Flask with HTTP instead or generate cert/key.")
        app.run(host="0.0.0.0", port=443, debug=False, use_reloader=False)
    else:
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

        self.referee_to_index = {
            "left": 0,
            "center": 1,
            "right": 2,
        }

        # Draw initial circles after canvas is ready
        self.root.after_idle(self.draw_circles)

        # Redraw on resize
        self.canvas.bind("<Configure>", lambda e: self.redraw_circles())

        # Check Flask queue periodically
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
                x - radius,
                center_y - radius,
                x + radius,
                center_y + radius,
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
            referee, color = color_queue.get()

            index = self.referee_to_index.get(referee)
            if index is None:
                continue  # ignore invalid referee

            if 0 <= index < len(self.circles):
                self.canvas.itemconfig(self.circles[index], fill=color)

        self.root.after(100, self.check_queue)


# ===========================
# Main entry point
# ===========================
if __name__ == "__main__":
    # Start Flask server in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Start Tkinter UI
    root = tk.Tk()
    app_ui = LightUI(root)
    root.mainloop()
