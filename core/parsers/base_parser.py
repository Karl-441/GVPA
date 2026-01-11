from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path, content):
        """
        Parse the content of a file and return a standardized analysis result.
        Result should be a dict with:
        - imports: list of strings
        - classes: list of dicts
        - functions: list of dicts
        - calls: list of dicts
        """
        pass
