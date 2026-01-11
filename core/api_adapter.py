from engine.image_vis_engine import ImageVisEngine
from engine.data_vis_engine import DataVisEngine
from engine.interactive_vis_engine import InteractiveVisEngine
from utils.logger import logger

class APIAdapter:
    def __init__(self):
        self.image_engine = ImageVisEngine()
        self.data_engine = DataVisEngine()
        self.interactive_engine = InteractiveVisEngine()

    def show_image(self, image_path, title="Image"):
        return self.image_engine.show_image(image_path, title)

    def plot_data(self, data, kind='line', title="Data Plot", x=None, y=None):
        return self.data_engine.plot_data(data, kind, title, x, y)

    def interactive_plot(self, data, kind='scatter', title="Interactive Plot", x=None, y=None, **kwargs):
        return self.interactive_engine.interactive_plot(data, kind, title, x, y, **kwargs)

api_adapter = APIAdapter()
