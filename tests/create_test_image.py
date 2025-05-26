"""Create test images for OCR testing."""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


def create_test_image_with_text(
    text: str, filename: str, width: int = 400, height: int = 200
):
    """Create a test image with specified text."""
    # Create white background
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # Try to use a system font, fallback to default if not available
    try:
        # macOS system font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        # Use default font
        font = ImageFont.load_default()

    # Calculate text position (centered)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text in black
    draw.text((x, y), text, fill="black", font=font)

    # Save image
    output_path = Path(__file__).parent / filename
    image.save(output_path)
    print(f"Created test image: {output_path}")
    return output_path


def create_simulator_like_image():
    """Create an image that mimics iOS Settings screen."""
    image = Image.new("RGB", (390, 844), color="#F2F2F7")  # iOS background color
    draw = ImageDraw.Draw(image)

    try:
        # Use SF Pro if available (macOS system font)
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
        item_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 17)
    except:
        title_font = ImageFont.load_default()
        item_font = ImageFont.load_default()

    # Draw navigation bar
    draw.rectangle([0, 0, 390, 96], fill="#F2F2F7")
    draw.text((20, 50), "Settings", fill="black", font=title_font)

    # Draw settings items
    items = [
        ("General", 120),
        ("Control Center", 170),
        ("Display & Brightness", 220),
        ("Home Screen", 270),
        ("Accessibility", 320),
        ("Wallpaper", 370),
        ("Siri & Search", 420),
        ("Face ID & Passcode", 470),
        ("Emergency SOS", 520),
        ("Battery", 570),
        ("Privacy & Security", 620),
    ]

    for text, y_pos in items:
        # Draw row background
        draw.rectangle([0, y_pos, 390, y_pos + 44], fill="white")
        # Draw separator line
        draw.line([20, y_pos + 43, 390, y_pos + 43], fill="#E5E5EA", width=1)
        # Draw text
        draw.text((20, y_pos + 12), text, fill="black", font=item_font)
        # Draw chevron (">")
        draw.text((360, y_pos + 12), ">", fill="#C7C7CC", font=item_font)

    output_path = Path(__file__).parent / "test_simulator_settings.png"
    image.save(output_path)
    print(f"Created simulator-like test image: {output_path}")
    return output_path


def create_ocr_test_suite():
    """Create a suite of test images for different OCR scenarios."""
    test_cases = [
        # Simple text
        ("Hello World", "test_hello_world.png"),
        ("Click Me", "test_click_me.png"),
        ("General", "test_general.png"),
        # Multiple occurrences
        ("Settings", "test_multiple_settings.png"),
        # Special characters
        ("Face ID & Passcode", "test_special_chars.png"),
        # Numbers
        ("Version 17.2.1", "test_numbers.png"),
    ]

    for text, filename in test_cases:
        create_test_image_with_text(text, filename)

    # Create simulator-like image
    create_simulator_like_image()


if __name__ == "__main__":
    create_ocr_test_suite()
    print("Test images created successfully!")
