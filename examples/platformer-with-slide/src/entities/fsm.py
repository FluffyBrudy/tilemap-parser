from typing import Generic, TypeVar

T = TypeVar("T", bound=object)


class BaseFsm(Generic[T]):
    """goal is to keep state pure, better.
    to avoid avoid forced transision and let state handler manage state
    if tempted to control explicitly use flags
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def enter(self, entity: T, /) -> None:
        pass

    def exit(self, entity: T, /):
        pass

    def get_next_state(self, T, /) -> str | None:
        return None

    def update(self, T, /) -> None:
        pass
