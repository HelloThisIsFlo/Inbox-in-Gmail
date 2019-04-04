from typing import NamedTuple, List


class Label(NamedTuple):
    id: str
    name: str


class Email(NamedTuple):
    id: str
    labels_ids: List[str]
