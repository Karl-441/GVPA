import cv2
import matplotlib.pyplot as plt
from utils.logger import logger

class ImageVisEngine:
    def __init__(self):
        pass

    def show_image(self, image_path, title="Image"):
        """Show image using OpenCV or Matplotlib"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return False
            
            # Convert to RGB for matplotlib if needed, but OpenCV imshow uses BGR
            cv2.imshow(title, img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return True
        except Exception as e:
            logger.error(f"Error showing image: {e}")
            return False

    def draw_shapes(self, image_path, shapes=[]):
        """Draw shapes on image"""
        # Placeholder for drawing shapes
        pass
