from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar


T = TypeVar('T')


class DatabaseRepositoryPort(ABC, Generic[T]):
    @abstractmethod
    def find_by_id(self, id_: int) -> T:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    def save(self, instance: T) -> T:
        raise NotImplementedError

    @abstractmethod
    def update(self, id_: int, instance: T) -> T:
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id_: int) -> None:
        raise NotImplementedError
