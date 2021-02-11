"""Super class for every node in the infrastructure network.
TODO: Add node busbar."""

import networkx as nx
import matplotlib.pyplot as plt
from math import floor
from elvis.battery import StationaryBattery


class InfrastructureNode:
    """Super class of all nodes (transformer, charging station, charging point)."""
    def __init__(self, identification, min_power, max_power,
                 parent=None):
        """Create an InfrastructureNode given all parameters.

        Args:
            identification: (str): ID of Node. Node type (transformer, charging station, charging
                point) followed by "_" and an increasing integer.
            max_power: (float): Maximum power allowed to go through node.
            min_power: (float): Minimum power allowed to go through node.
            parent: (obj): Depending on position in graph the obj differs:
                transformer         -> parent = None
                charging station    -> parent = :obj: `infrastructure_node.Transformer`
                charging point      -> parent = :obj: `charging_point.ChargingPoint`
        Raises:
            AssertionError:
                - If min_power and max_power are not numerical (int or float).
                - If parent is not an instance of :obj: `infrastructure_node.InfrastructureNode.

        """

        assert type(min_power) is int or type(min_power) is float
        assert type(max_power) is int or type(max_power) is float

        self.id = str(identification)
        self.min_power = min_power
        self.max_power = max_power

        assert parent is None or isinstance(parent, InfrastructureNode)
        self.parent = parent
        if parent is not None:
            parent.add_child(self)
        self.children = []
        self.leafs = None

    def add_child(self, child):
        """Add child to list of all children."""
        assert isinstance(child, InfrastructureNode)
        if child not in self.children:
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
        for cs in transformer.children:
            graph.add_node(cs)
            graph.add_edge(transformer, cs)
            # add charging points to graph
            for cp in cs.children:
                graph.add_node(cp)
                graph.add_edge(cs, cp)

        nx.draw(graph, with_labels=True)
        plt.show()

    def get_leaf_nodes(self):
        leafs = []

        def _get_leaf_nodes(node):
            if len(node.children) == 0:
                leafs.append(node)
            for n in node.children:
                _get_leaf_nodes(n)

        _get_leaf_nodes(self)
        return leafs

    def set_up_leafs(self):
        self.leafs = self.get_leaf_nodes()

        def _set_up_leafs(node):
            if len(node.children) == 0:
                return
            for n in node.children:
                n.leafs = n.get_leaf_nodes()
                _set_up_leafs(n)
        _set_up_leafs(self)

    def get_transformer(self):
        parent = self
        go_on = True
        while go_on is True:
            if parent.parent is not None:
                parent = parent.parent
                # If the parent is the Transformer return it
                if isinstance(parent, Transformer):
                    return parent
            else:
                go_on = False

        return None


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

    def max_hardware_power(self, power_assigned, preload):
        """Calculate max power assignable to the transformer considering ints limits and already
            assigned power.

            Args:
                power_assigned: (dict): Containing all :obj: `charging_point.ChargingPoint`
                    in the infrastructure and their currently assigned power.
                preload: (float): Preload at the transformer in kWh.

            Returns:
                max_power: (float): Max power that can be assigned to the transformer.
        """
        power_already_assigned = preload
        for leaf in self.leafs:
            if not isinstance(leaf, Storage):
                power_already_assigned += power_assigned[leaf]

        max_power = max(self.max_power - power_already_assigned, 0)
        max_power = floor(max_power * 1000) / 1000

        return max_power


class Storage(InfrastructureNode):
    # ID counter
    counter = 1

    def __init__(self, stationary_battery, transformer):
        assert isinstance(stationary_battery, StationaryBattery)
        self.storage = stationary_battery

        # Power limits
        max_power = self.storage.max_charge_power
        min_power = self.storage.min_charge_power

        # ID
        identification = 'Storage_System ' + str(Storage.counter)
        Storage.counter += 1

        super().__init__(identification, max_power, min_power, parent=transformer)
