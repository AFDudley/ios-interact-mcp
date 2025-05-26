#!/usr/bin/env python3
"""Test coordinate flip hypothesis for General and Camera"""

import asyncio
from ocr_controller import SimulatorWindowManager
from ocrmac import ocrmac
from PIL import Image, ImageDraw
import os


async def main():
    # Take fullscreen screenshot
    print("Taking fullscreen screenshot...")
    screenshot_path = await SimulatorWindowManager.capture_simulator_screenshot(
        use_fullscreen=True
    )
    print(f"Screenshot saved to: {screenshot_path}")

    # Run OCR
    print("\nRunning OCR...")
    annotations = ocrmac.OCR(screenshot_path).recognize()

    # Load image
    img = Image.open(screenshot_path)
    img_width, img_height = img.size
    print(f"Image size: {img_width}x{img_height}")

    # Create drawing context
    draw = ImageDraw.Draw(img)

    # Find and draw both General and Camera
    for target_text in ["General", "Camera"]:
        for ann in annotations:
            text, confidence, bounds = ann
            if text == target_text:
                x_norm, y_norm, width_norm, height_norm = bounds

                # Convert to pixel coordinates with flipped y
                x = x_norm * img_width
                width = width_norm * img_width
                height = height_norm * img_height
                y = (
                    1 - y_norm - height_norm
                ) * img_height  # Flip y with normalized height

                print(f"\nFound '{target_text}':")
                print(
                    f"  Normalized bounds: x={x_norm:.4f}, y={y_norm:.4f}, w={width_norm:.4f}, h={height_norm:.4f}"
                )
                print(
                    f"  Pixel bounds: x={x:.0f}, y={y:.0f}, w={width:.0f}, h={height:.0f}"
                )
                print(
                    f"  Bounding box: ({x:.0f}, {y:.0f}) to ({x+width:.0f}, {y+height:.0f})"
                )

                # Draw red bounding box
                bbox = (x, y, x + width, y + height)
                draw.rectangle(bbox, outline="red", width=3)
                break

    # Save image with bounding boxes
    output_path = "coordinate_flip_test.png"
    img.save(output_path)
    print(f"\nImage with bounding boxes saved to: {output_path}")

    # Exit fullscreen
    await SimulatorWindowManager.exit_fullscreen()


if __name__ == "__main__":
    asyncio.run(main())
