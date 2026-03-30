import os
import numpy as np
from PIL import Image

def parse_color(color):
    if isinstance(color, tuple) and len(color) == 3:
        return color

    if isinstance(color, str):
        color = color.lstrip("#")
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    raise ValueError("Invalid color format")

def batch_recolor_fast(folder, color):
    new_color = parse_color(color)

    for filename in os.listdir(folder):
        if filename.lower().endswith(".png"):
            path = os.path.join(folder, filename)

            img = Image.open(path).convert("RGBA")
            data = np.array(img)

            mask = data[:, :, 3] > 0
            data[mask, 0:3] = new_color

            new_img = Image.fromarray(data)
            new_img.save(path)

            print(f"Processed: {filename}")

# Examples:
#batch_recolor_fast(".", "#efdefa")     # hex with #
#batch_recolor_fast(".", "00ccff")      # hex without #
#batch_recolor_fast(".", (255, 100, 0)) # RGB tuple
