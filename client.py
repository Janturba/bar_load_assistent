import tkinter as tk
from tkinter import font
import tkinter.messagebox as messagebox
import json
import re
import hashlib

# --------------------------------------------------
# Configuration
# --------------------------------------------------

WEIGHT_FILE = "./config_data/weight.json"
PLATES_WEIGHT_FILE = "./config_data/plates_weight.json"
PLATES_COLOUR_FILE = "./config_data/plates_colours.json"

CHECK_INTERVAL_MS = 3000  # 3 seconds

last_weight_hash = None
current_info = None

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def md5_of_file(path, chunk_size=8192):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)
    return md5.hexdigest()

def get_json_value(filename, key):
    with open(filename, 'r') as f:
        data = json.load(f)
        return data.get(key)

def load_lifter_info(filename=WEIGHT_FILE):
    with open(filename, "r") as f:
        return json.load(f)

# --------------------------------------------------
# Refresh logic
# --------------------------------------------------

def refresh_lifter(weight_value=None):
    global current_info

    if weight_value is None or str(weight_value).strip() == "":
        current_info = load_lifter_info()
        update_display(current_info)
        return

    m = re.search(r'[-+]?\d*\.?\d+', str(weight_value))
    if not m:
        messagebox.showerror("Invalid input", "Could not parse a number.")
        return

    weight_num = float(m.group())

    if weight_num < 25:
        messagebox.showwarning(
            "Invalid weight",
            "Weight must be at least 25 kg (bar + collars)."
        )
        return

    current_info = {
        "first": "Manual Entry",
        "declared_weight": weight_num
    }
    update_display(current_info)

# --------------------------------------------------
# Plate math
# --------------------------------------------------

def get_plates(total_weight, disk_weight):
    count = int(total_weight // disk_weight)
    if count % 2 != 0:
        count -= 1
    remainder = total_weight - (count * disk_weight)
    return max(count, 0), remainder

def load_bar(weight):
    barless_weight = weight - 25  # bar + collars
    plates = {}

    for name, disk in [
        ("Red", 25),
        ("Blue", 20),
        ("Yellow", 15),
        ("Green", 10),
        ("White", 5),
        ("Black", 2.5),
        ("Silver", 1.25)
    ]:
        count, barless_weight = get_plates(barless_weight, disk)
        if count:
            plates[name] = count

    return plates

# --------------------------------------------------
# Drawing
# --------------------------------------------------

def draw_plate(canvas, x, y, w, h, text, color, font_color):
    canvas.create_rectangle(
        x, y, x + w, y + h,
        fill=color,
        outline="black",
        width=2
    )
    canvas.create_text(
        x + w / 2,
        y + h / 2,
        text=text,
        font=("Arial", max(10, int(h * 0.08)), "bold"),
        fill=font_color
    )

def update_display(info):
    lifter_label.config(text=info.get("first", ""))
    weight_label.config(text=f"{info.get('declared_weight', '')} kg")

    canvas.delete("all")
    root.update_idletasks()

    plates = load_bar(info["declared_weight"])

    canvas_w = canvas.winfo_width()
    canvas_h = canvas.winfo_height()

    if canvas_w < 50 or canvas_h < 50:
        return

    plate_height = int(canvas_h * 0.8)
    plate_width = int(plate_height * 0.35)

    plate_pairs = sum(v // 2 for v in plates.values())
    total_width = plate_pairs * (plate_width + 10)

    x = max((canvas_w - total_width) // 2, 20)
    y = int(canvas_h * 0.1)

    for plate_name, count in plates.items():
        weight_val = float(get_json_value(PLATES_WEIGHT_FILE, plate_name))
        color = get_json_value(PLATES_COLOUR_FILE, plate_name)

        font_color = "black" if weight_val in (1.25, 5) else "white"

        for _ in range(count // 2):
            draw_plate(
                canvas,
                x, y,
                plate_width,
                plate_height,
                str(weight_val),
                color,
                font_color
            )
            x += plate_width + 10

# --------------------------------------------------
# File watcher (MD5 polling)
# --------------------------------------------------

def check_weight_file():
    global last_weight_hash, current_info

    try:
        new_hash = md5_of_file(WEIGHT_FILE)
    except FileNotFoundError:
        root.after(CHECK_INTERVAL_MS, check_weight_file)
        return

    if last_weight_hash is None:
        last_weight_hash = new_hash

    elif new_hash != last_weight_hash:
        print("weight.json changed → refreshing")
        last_weight_hash = new_hash
        current_info = load_lifter_info()
        update_display(current_info)

    root.after(CHECK_INTERVAL_MS, check_weight_file)

# --------------------------------------------------
# GUI setup
# --------------------------------------------------

root = tk.Tk()
root.title("Powerlifting Display")
root.configure(bg="grey26")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

header_font = font.Font(family="Helvetica", size=32, weight="bold")
sub_font = font.Font(family="Helvetica", size=20)
weight_font = font.Font(family="Helvetica", size=50, weight="bold")

weight_label = tk.Label(root, font=weight_font, fg="cyan", bg="grey26")
lifter_label = tk.Label(root, font=weight_font, fg="cyan", bg="grey26")

plates_frame = tk.Frame(root, bg="grey26")
canvas = tk.Canvas(plates_frame, bg="grey26", highlightthickness=0)

weight_label.pack(pady=(10, 0))
lifter_label.pack(pady=(10, 0))
plates_frame.pack(fill="both", expand=True, pady=(20, 0))
canvas.pack(fill="both", expand=True)

# Control window
control_window = tk.Toplevel(root)
control_window.title("Lifter Controls")
control_window.geometry("300x150")
control_window.configure(bg="grey16")
control_window.protocol("WM_DELETE_WINDOW", control_window.withdraw)

weight_entry = tk.Entry(control_window, font=sub_font, justify="center")
weight_entry.pack(pady=20)

refresh_button = tk.Button(
    control_window,
    text="Refresh Lifter",
    command=lambda: refresh_lifter(weight_entry.get()),
    font=sub_font,
    bg="gray30",
    fg="white"
)
refresh_button.pack()

weight_entry.bind("<Return>", lambda e: refresh_lifter(weight_entry.get()))

# --------------------------------------------------
# Startup
# --------------------------------------------------

current_info = load_lifter_info()
last_weight_hash = md5_of_file(WEIGHT_FILE)

root.update_idletasks()
update_display(current_info)

check_weight_file()

root.mainloop()
