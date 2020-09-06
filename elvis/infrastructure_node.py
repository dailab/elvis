"""Super class for every node in the infrastructure network.
TODO: Add node busbar."""

import networkx as nx
import matplotlib.pyplot as plt


class InfrastructureNode:
    """Super class of all nodes (transformer, charging point, connection point)."""
    def __init__(self, identification, min_power, max_power,
                 parent=None):
        """Create an InfrastructureNode given all parameters.

        Args:
            identification: (str): ID of Node. Node type (transformer, charging point, connection
                point) followed by "_" and an increasing integer.
            max_power: (float): Maximum power allowed to go through node.
            min_power: (float): Minimum power allowed to go through node.
            parent: (obj): Depending on position in graph the obj differs:
                transformer      -> child = None
                charging point   -> child = :obj: `infrastructure_node.Transformer`
                connection point -> child = :obj: `connection_point.ConnectionPoint`
        Raises:
            AssertionError:
                - If min_power and max_power are not numerical (int or float).
                - If parent is not an instance of :obj: `infrastructure_node.InfrastructureNode.

        """

        assert type(min_power) is int or type(min_power) is float
        assert type(max_power) is int or type(min_power) is float

        self.id = str(identification)
        self.min_power = min_power
        self.max_power = max_power

        assert parent is None or isinstance(parent, InfrastructureNode)
        self.parent = parent
        self.children = []

    def add_child(self, child):
        """Add child to list of all children."""
        assert isinstance(child, InfrastructureNode)
        self.children.append(child)

    def draw_infrastructure(self):
        """Displays a window with a graph of the infrastructure."""
        graph = nx.Graph()

        # find transformer as the root of the tree
        parent = self
        go_on = True
        while go_on:
            if isinstance(parent.parent, InfrastructureNode):
                parent = parent.parent
                go_on = True
            else:  # type(parent.parent) is None -> root found
                go_on = False
        transformer = parent

        # add transformer to graph
        graph.add_node(transformer)

        # add charging points to graph
        for charging_point in transformer.children:
            graph.add_node(charging_point)
            graph.add_edge(transformer, charging_point)
            # add connection points to graph
            for connection_point in charging_point.children:
                graph.add_node(connection_point)
                graph.add_edge(charging_point, connection_point)

        nx.draw(graph, with_labels=True)
        plt.show()


class Transformer(InfrastructureNode):
    """Represents a transformer. No usability besides having a max and min power.
    Does not have a parent node in infrastructure."""
    counter = 1

    def __init__(self, min_power, max_power):

        identification = 'Transformer_' + str(Transformer.counter)
        Transformer.counter += 1

        super().__init__(identification, min_power, max_power)

    def __str__(self):
        return str(self.id)
