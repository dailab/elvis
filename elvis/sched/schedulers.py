
class SchedulingPolicy:
    def schedule(self, config):
        """Subclasses should override this with their scheduling implementation."""
        raise NotImplementedError()


class Uncontrolled(SchedulingPolicy):
    """Implements the 'Uncontrolled' scheduling policy."""

    def schedule(self, config):
        pass


class FCFS(SchedulingPolicy):
    """Implements the 'First Come First Serve' scheduling policy."""

    def schedule(self, config):
        pass


class WithStorage(SchedulingPolicy):
    """Implements the 'Storage' scheduling policy."""

    def schedule(self, config):
        pass


class DiscriminationFree(SchedulingPolicy):
    """Implements the 'Discrimination Free' scheduling policy."""

    def schedule(self, config):
        pass


class Optimized(SchedulingPolicy):
    """Implements the 'Optimized' scheduling policy."""

    def schedule(self, config):
        pass
