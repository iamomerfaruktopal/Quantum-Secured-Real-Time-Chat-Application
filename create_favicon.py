try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Installing Pillow (PIL)...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw

# Create a 32x32 black image
img = Image.new('RGB', (32, 32), color='black')
d = ImageDraw.Draw(img)

# Create static directory if it doesn't exist
import os
if not os.path.exists('static'):
    os.makedirs('static')

# Draw a simple Q in white
d.text((8, 4), "Q", fill='white')  # Removed size parameter as it's not supported in older versions

# Save as ICO
img.save('static/favicon.ico')
print("Favicon created successfully in static/favicon.ico") 