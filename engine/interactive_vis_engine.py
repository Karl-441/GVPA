import plotly.express as px
import plotly.io as pio
import pandas as pd
from utils.logger import logger

class InteractiveVisEngine:
    def __init__(self):
        pass

    def interactive_plot(self, data, kind='scatter', title="Interactive Plot", x=None, y=None, **kwargs):
        """
        Create interactive plot using Plotly
        """
        try:
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            if kind == 'scatter':
                fig = px.scatter(data, x=x, y=y, title=title, **kwargs)
            elif kind == 'line':
                fig = px.line(data, x=x, y=y, title=title, **kwargs)
            elif kind == 'bar':
                fig = px.bar(data, x=x, y=y, title=title, **kwargs)
            else:
                logger.warning(f"Unsupported plot kind: {kind}")
                return False
            
            fig.show()
            return True
        except Exception as e:
            logger.error(f"Error creating interactive plot: {e}")
            return False
