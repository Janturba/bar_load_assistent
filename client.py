import tkinter as tk
from tkinter import font
import json

# --- Load lifter info from file ---
def load_lifter_info(filename="weight.json"):
    with open(filename, "r") as f:
        return json.load(f)

# --- Button action ---
def refresh_lifter():
    new_info = load_lifter_info()
    update_display(new_info)

plate_colors = {
"Red": "red",
"Blue": "blue",
"Yellow": "gold",
"Green": "green",
"White": "white",
"Black": "black",
"Silver": "silver"
}

plate_weights = {
"Red": "25",
"Blue": "20",
"Yellow": "15",
"Green": "10",
"White": "5",
"Black": "2.5",
"Silver": "1.25"
}

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

def draw_plate(canvas, x, y, width, height, text, color):
    rect = canvas.create_rectangle(
    x, y, x + width, y + height,
    fill=color, outline="black"
    )
    text_item = canvas.create_text(
    x + width / 2, y + height / 2,
    text=text, font=("Arial", int(height * 0.07), "bold"), fill="white"
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
            weight_value = plate_weights[color]
            draw_plate(canvas, x, y, plate_width, plate_height, weight_value, plate_colors[color])
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

# Button
refresh_button = tk.Button(root, text="Refresh Lifter", command=refresh_lifter)

# Layout
weight_label.pack(pady=(10, 0))
plates_frame.pack(fill="both", expand=True, pady=(20, 0))
refresh_button.pack(pady=(20, 20))

# Initial load
lifter_info = load_lifter_info()
update_display(lifter_info)

root.mainloop()
