import matplotlib.pyplot as plt
import pandas as pd
from utils.logger import logger

class DataVisEngine:
    def __init__(self):
        pass

    def plot_data(self, data, kind='line', title="Data Plot", x=None, y=None):
        """
        Plot data using Matplotlib
        data: pandas DataFrame or list/dict
        kind: 'line', 'bar', 'scatter', etc.
        """
        try:
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)
            
            plt.figure(figsize=(10, 6))
            if kind == 'line':
                if x and y:
                    plt.plot(data[x], data[y])
                else:
                    data.plot()
            elif kind == 'bar':
                if x and y:
                    plt.bar(data[x], data[y])
                else:
                    data.plot(kind='bar')
            elif kind == 'scatter':
                if x and y:
                    plt.scatter(data[x], data[y])
                else:
                    logger.warning("Scatter plot requires x and y columns")
            
            plt.title(title)
            plt.show()
            return True
        except Exception as e:
            logger.error(f"Error plotting data: {e}")
            return False
