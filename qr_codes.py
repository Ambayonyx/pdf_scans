import re
import uuid
from enum import Enum
from typing import Optional


class Side(Enum):
    FRONT = "FRONT"
    BACK = "BACK"


class QrCode:
    FORMAT_REGEX = r"AMBAYONYX SEP_PAGE: (?P<uuid>[\dabcdef]{8}-[\dabcdef]{4}-[\dabcdef]{4}-[\dabcdef]{4}-[\dabcdef]{12}) : (?P<side>FRONT|BACK)"

    def __init__(self, side: Side, identifier: Optional[uuid.UUID] = None):
        if not identifier:
            identifier = uuid.uuid4()

        self._regex = None
        self._side = side
        self._id = identifier

    def set_from_scanned_text(self, text: str) -> None:
        if not self._regex:
            self._regex = re.compile(QrCode.FORMAT_REGEX)
        matches = self._regex.search(text)
        self._id = matches.group("uuid")
        self._side = Side[matches.group("side")]

    def __str__(self):
        return f'AMBAYONYX SEP_PAGE: {self._id} : {self._side}'
