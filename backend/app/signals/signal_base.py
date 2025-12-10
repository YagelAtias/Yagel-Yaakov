from abc import ABC, abstractmethod

class DistressSignal(ABC):
    """
    Abstract Base Class for any distress indicator (Text, Audio, or Behavior).
    """

    @abstractmethod
    def analyze(self, data: any ) -> dict:
        """
        Input: Raw data (text string or audio bytes).
        Output: Dictionary containing 'score' (0.0-1.0) and 'metadata'.
        """
        pass