
class ElvisResult:
    """Represents the result of an Elvis simulation. 

    Don't use this directly, instead pass it to one of the provided functions for evaluating Elvis results.
    """

    def __init__(self):
        pass

    def to_yaml(self):
        """Serialize this ElvisResult to a yaml string."""

        pass

    def to_csv(self, file_name):
        """Serialize this ElvisResult to a CSV file."""

        pass

    @staticmethod
    def from_yaml(yaml_str):
        """Create an ElvisResult from a yaml string."""

        pass

    @staticmethod
    def from_json(json_str):
        """Create an ElvisResult from a yaml string."""

        pass

    @staticmethod
    def from_csv(file_name):
        """Create an ElvisResult from a CSV file."""

        pass
