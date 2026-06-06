from typing import Any, Dict, Generic, TypeVar

TEntity = TypeVar("TEntity")


class FsmBase(Generic[TEntity]):
    def __init__(self, name: str) -> None:
        self.name = name

    def enter(self, sentity: TEntity, /) -> None:
        pass

    def exit(self, entity: TEntity, /) -> None:
        pass

    def get_next_state(self, entity: TEntity, /, **kwargs) -> None | str:
        return None

    def update(self, entity: TEntity, /) -> None:
        pass
