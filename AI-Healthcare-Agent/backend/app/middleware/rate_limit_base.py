from abc import ABC, abstractmethod


class RateLimiter(ABC):
    @abstractmethod
    def check(self, key: str, route: str, max_hits: int, window_seconds: int) -> tuple[bool, int]:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    @abstractmethod
    def check_login(self, key: str) -> tuple[bool, int]:
        ...

    @abstractmethod
    def check_global(self, key: str) -> tuple[bool, int]:
        ...
