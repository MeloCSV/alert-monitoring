from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

T = TypeVar("T")


class UseCaseServicePort(ABC, Generic[T]):

    @abstractmethod
    def list_all(self) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    def get(self, id_: int) -> T:
        raise NotImplementedError

    @abstractmethod
    def create(self, instance: T) -> T:
        raise NotImplementedError

    @abstractmethod
    def update(self, id_: int, instance: T) -> T:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id_: int) -> None:
        raise NotImplementedError
