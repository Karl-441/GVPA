import networkx as nx
import matplotlib.pyplot as plt
import io
from utils.logger import logger

class StructureVisualizer:
    def __init__(self):
        pass

    def create_class_diagram(self, analysis_data):
        """
        Create a class structure diagram from analysis data
        Returns: BytesIO object containing the image
        """
        try:
            G = nx.DiGraph()
            
            # Add nodes and edges
            for cls in analysis_data.get("classes", []):
                class_node = f"Class: {cls['name']}"
                G.add_node(class_node, color='lightblue', shape='box')
                
                # Bases
                for base in cls['bases']:
                    base_node = f"Base: {base}"
                    G.add_node(base_node, color='lightgray', shape='ellipse')
                    G.add_edge(base_node, class_node, label="inherits")
                
                # Methods
                for method in cls['methods']:
                    method_node = f"{method['name']}()"
                    G.add_node(method_node, color='lightgreen', shape='ellipse')
                    G.add_edge(class_node, method_node, label="has")

            # Global functions
            for func in analysis_data.get("functions", []):
                func_node = f"Func: {func['name']}()"
                G.add_node(func_node, color='lightyellow', shape='ellipse')

            if G.number_of_nodes() == 0:
                return None

            # Draw
            plt.figure(figsize=(10, 8))
            pos = nx.spring_layout(G, k=0.5, iterations=50)
            
            # Draw nodes
            colors = [G.nodes[n].get('color', 'white') for n in G.nodes]
            nx.draw(G, pos, with_labels=True, node_color=colors, 
                    node_size=2000, font_size=8, font_weight='bold', 
                    arrows=True, edge_color='gray')
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            buf.seek(0)
            return buf
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return None

structure_visualizer = StructureVisualizer()
