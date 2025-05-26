"""Debug OCR format to understand the actual output."""

from pathlib import Path
from ocrmac import ocrmac

# Test with a simple image
image_path = Path(__file__).parent / "test_hello_world.png"
print(f"Testing OCR on: {image_path}")

# Run OCR
annotations = ocrmac.OCR(str(image_path)).recognize()

print(f"\nNumber of annotations: {len(annotations)}")
print(f"Type of annotations: {type(annotations)}")

if annotations:
    print("\nFirst annotation:")
    print(f"Type: {type(annotations[0])}")
    print(f"Content: {annotations[0]}")

    # Try to access individual elements
    if len(annotations[0]) >= 3:
        print(f"\nElement 0 (text): {annotations[0][0]}")
        print(f"Element 1 (bounds): {annotations[0][1]}")
        print(f"Element 2 (confidence): {annotations[0][2]}")
        print(f"Type of bounds: {type(annotations[0][1])}")
