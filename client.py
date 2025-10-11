import tkinter as tk
from tkinter import font
import tkinter.messagebox as messagebox
import json
import re

def get_weight_and_color(filename, key):
    with open(filename, 'r') as f:
        data = json.load(f)
        return data.get(key)

# --- Load lifter info from file ---
def load_lifter_info(filename="weight.json"):
    with open(filename, "r") as f:
        return json.load(f)

# --- Button action (now accepts optional input) ---
def refresh_lifter(weight_value=None):
    """
    If weight_value is empty/None -> load from JSON.
    Otherwise try to parse a numeric weight from the string and use it.
    """
    # empty -> load from file
    if weight_value is None or str(weight_value).strip() == "":
        try:
            new_info = load_lifter_info()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {e}")
            return
        update_display(new_info)
        return

    # try to extract a number (accepts "90", "90kg", "90.5", etc.)
    s = str(weight_value).strip().lower()
    m = re.search(r'[-+]?\d*\.?\d+', s)
    if not m:
        messagebox.showerror("Invalid input", "Could not parse a number from the input. Using saved value.")
        try:
            new_info = load_lifter_info()
            update_display(new_info)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load fallback value: {e}")
        return

    try:
        weight_num = float(m.group())
    except ValueError:
        messagebox.showerror("Invalid input", "Parsed value is not a valid number. Using saved value.")
        try:
            new_info = load_lifter_info()
            update_display(new_info)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load fallback value: {e}")
        return

    # basic sanity check
    if weight_num < 25:
        messagebox.showwarning("Weight too low", "Declared weight must be at least 25 kg (bar + collars).")
        return

    # build same structure your update_display expects
    info = {"declared_weight": weight_num}
    update_display(info)

def get_plates(total_weight, disk_type):
    quotient = int(total_weight // disk_type)  # ensure it's an integer
    if quotient % 2 != 0:  # odd disk not allowed!
        quotient -= 1
        remainder = total_weight - quotient * disk_type
        if quotient > 0:
            return quotient, remainder
        else:
            quotient = 0
            return quotient, remainder
    else:
        remainder = total_weight - quotient * disk_type
        return quotient, remainder

def calculate_plates(weight):
    """Return a dictionary of plates to load for given bar weight"""
    barless_weight = weight - 25  # remove bar + collars
    print(f"Removing bar and collars: {barless_weight}kg")
    plates = {}
    reds, remainder = get_plates(barless_weight, 25)
    if reds: plates["Red"] = reds
    blues, remainder = get_plates(remainder, 20)
    if blues: plates["Blue"] = blues
    yellows, remainder = get_plates(remainder, 15)
    if yellows: plates["Yellow"] = yellows
    greens, remainder = get_plates(remainder, 10)
    if greens: plates["Green"] = greens
    whites, remainder = get_plates(remainder, 5)
    if whites: plates["White"] = whites
    blacks, remainder = get_plates(remainder, 2.5)
    if blacks: plates["Black"] = blacks
    silvers, remainder = get_plates(remainder, 1.25)
    if silvers: plates["Silver"] = silvers
    return plates

def draw_plate(canvas, x, y, width, height, text, color, font_color):
    rect = canvas.create_rectangle(
        x, y, x + width, y + height,
        fill=color, outline="black"
    )
    text_item = canvas.create_text(
        x + width / 2, y + height / 2,
        text=text, font=("Arial", int(height * 0.07), "bold"), fill=font_color
    )
    return rect, text_item

def update_display(info):
    weight_label.config(text=f"{info['declared_weight']} kg")

    # Clear canvas
    canvas.delete("all")

    # Calculate plates
    plates = calculate_plates(info['declared_weight'])

    # --- Auto scaling ---
    num_plates = sum(count // 2 for count in plates.values())
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    if num_plates > 0:
        # plate height is a fraction of canvas height
        plate_height = int(canvas_height * 0.8)
        # keep a realistic aspect ratio (plates are tall and thin)
        plate_width = int(plate_height * 0.35)
        # total width needed for all plates + spacing
        total_width = num_plates * (plate_width + 10)
        # center plates if they don't fill canvas
        start_x = max((canvas_width - total_width) // 2, 20)
    else:
        plate_height = int(canvas_height * 0.8)
        plate_width = int(plate_height * 0.35)
        start_x = 50

    y = int(canvas_height * 0.1)

    # Draw plates
    x = start_x
    for color, count in plates.items():
        for _ in range(count // 2):
            weight_value = get_weight_and_color('./config_data/plates_weight.json', color)
            if weight_value == "5":
                draw_plate(canvas, x, y, plate_width, plate_height, weight_value, get_weight_and_color('./config_data/plates_colours.json', color), font_color="black")
            elif weight_value == "1.25":
                draw_plate(canvas, x, y, plate_width, plate_height, weight_value, get_weight_and_color('./config_data/plates_colours.json', color), font_color="black")
            else:
                draw_plate(canvas, x, y, plate_width, plate_height, weight_value, get_weight_and_color('./config_data/plates_colours.json', color), font_color="white")
            x += plate_width + 10

# --- GUI setup ---
root = tk.Tk()
root.title("Powerlifting Display")
root.configure(bg="grey26")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))

# Fonts
header_font = font.Font(family="Helvetica", size=32, weight="bold")
sub_font = font.Font(family="Helvetica", size=20)
weight_font = font.Font(family="Helvetica", size=120, weight="bold")

# Labels
weight_label = tk.Label(root, text="", font=weight_font, fg="cyan", bg="grey26")

plates_frame = tk.Frame(root, bg="grey26")
canvas = tk.Canvas(plates_frame, bg="grey26", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# Create a separate control window
control_window = tk.Toplevel(root)
control_window.title("Lifter Controls")
control_window.geometry("300x150")
control_window.configure(bg="grey16")

# Make sure closing the control window doesn't close the app
control_window.protocol("WM_DELETE_WINDOW", lambda: control_window.withdraw())

# Layout
weight_label.pack(pady=(10, 0))
plates_frame.pack(fill="both", expand=True, pady=(20, 0))

weight_entry = tk.Entry(control_window, font=sub_font, justify="center")
weight_entry.pack(pady=(0, 20))

# Add Refresh button to the new control window
refresh_button = tk.Button(
    control_window,
    text="Refresh Lifter",
    command=lambda: refresh_lifter(weight_entry.get()),  # pass input to function
    font=sub_font,
    bg="gray30",
    fg="white"
)
refresh_button.pack(pady=10)

# allow pressing Enter in the entry to trigger refresh
weight_entry.bind("<Return>", lambda e: refresh_lifter(weight_entry.get()))

# Initial load
lifter_info = load_lifter_info()
update_display(lifter_info)

# pre-fill entry with saved value
weight_entry.delete(0, tk.END)
weight_entry.insert(0, str(lifter_info.get("declared_weight", "")))

root.mainloop()
