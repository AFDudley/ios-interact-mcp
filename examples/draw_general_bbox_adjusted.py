#!/usr/bin/env python3
"""Take screenshot and draw bounding box for General with vertical adjustment"""

import asyncio
from ocr_controller import SimulatorWindowManager
from ocrmac import ocrmac
from PIL import Image, ImageDraw


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

    # Find General
    general_found = False
    for ann in annotations:
        text, confidence, bounds = ann
        if text == "General":
            x_norm, y_norm, width_norm, height_norm = bounds

            # Convert to pixel coordinates
            x = x_norm * img_width
            width = width_norm * img_width
            height = height_norm * img_height
            y = (1 - y_norm) * img_height  # Test bottom-left origin hypothesis

            print("\nFound 'General':")
            print(
                f"  Normalized bounds: x={x_norm:.4f}, y={y_norm:.4f}, "
                f"w={width_norm:.4f}, h={height_norm:.4f}"
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

            # Draw center point
            center_x = x + width / 2
            center_y = y + height / 2
            draw.ellipse(
                (center_x - 5, center_y - 5, center_x + 5, center_y + 5), fill="red"
            )
            print(f"  Center: ({center_x:.0f}, {center_y:.0f})")

            general_found = True
            break

    if general_found:
        # Save image with bounding box in current directory
        output_path = "general_bbox_adjusted.png"
        img.save(output_path)
        print(f"\nImage with bounding box saved to: {output_path}")
    else:
        print("\n'General' text not found in OCR results")

    # Exit fullscreen
    await SimulatorWindowManager.exit_fullscreen()


if __name__ == "__main__":
    asyncio.run(main())
