from abc import ABC, abstractmethod
from collections.abc import Iterator, MutableMapping
from datetime import datetime, timezone
from typing import Any


class Entity(ABC):
    @abstractmethod
    def identity(self) -> tuple[Any, ...]:
        """Return the value used to compare entities."""

    def __eq__(self, other):
        return type(self) is type(other) and self.identity() == other.identity()

    def __repr__(self):
        return f"{type(self).__name__}({self.identity()!r})"

    def __str__(self):
        return repr(self)


class FieldMap(Entity, MutableMapping):
    """Small ordered mapping used instead of built-in dictionaries."""

    def __init__(self, pairs=()):
        self._items = []
        self.pairs = pairs

    @property
    def pairs(self):
        return tuple(self._items)

    @pairs.setter
    def pairs(self, values):
        self._items = []
        for key, value in values:
            self[key] = value

    @classmethod
    def from_pairs(cls, pairs):
        return cls(pairs)

    def identity(self):
        return tuple(self._items)

    def __getitem__(self, key):
        for stored_key, value in self._items:
            if stored_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("FieldMap keys must be strings")
        for index, (stored_key, _) in enumerate(self._items):
            if stored_key == key:
                self._items[index] = (key, value)
                return
        self._items.append((key, value))

    def __delitem__(self, key):
        for index, (stored_key, _) in enumerate(self._items):
            if stored_key == key:
                del self._items[index]
                return
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return f"FieldMap({self._items!r})"

    def __str__(self):
        return "{" + ", ".join(f"{key}: {value}" for key, value in self._items) + "}"


class Entry(Entity):
    def __init__(self, site="", login="", password="", note=""):
        self.site = site
        self.login = login
        self.password = password
        self.note = note

    @property
    def site(self):
        return self._site

    @site.setter
    def site(self, value):
        self._site = str(value).strip()

    @property
    def login(self):
        return self._login

    @login.setter
    def login(self, value):
        self._login = str(value).strip()

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = str(value)

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        self._note = str(value).strip()

    def identity(self):
        return self.site, self.login, self.password, self.note

    def to_fields(self):
        return FieldMap(
            (
                ("site", self.site),
                ("login", self.login),
                ("password", self.password),
                ("note", self.note),
            )
        )

    @classmethod
    def from_fields(cls, fields):
        return cls(
            fields["site"],
            fields["login"],
            fields["password"],
            fields["note"],
        )

    def __eq__(self, other):
        return isinstance(other, Entry) and self.identity() == other.identity()

    def __repr__(self):
        return (
            f"Entry(site={self.site!r}, login={self.login!r}, "
            f"password=<redacted>, note={self.note!r})"
        )

    def __str__(self):
        return f"{self.site} ({self.login})"


class EntryCollection(Entity):
    def __init__(self, entries=()):
        self.entries = entries

    @property
    def entries(self):
        return tuple(self._entries)

    @entries.setter
    def entries(self, values):
        entries = list(values)
        if not all(isinstance(entry, Entry) for entry in entries):
            raise TypeError("EntryCollection only accepts Entry objects")
        self._entries = entries

    def identity(self):
        return tuple(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, index):
        return self._entries[index]

    def add(self, entry):
        if not isinstance(entry, Entry):
            raise TypeError("Expected an Entry")
        self._entries.append(entry)

    def replace(self, index, entry):
        if not isinstance(entry, Entry):
            raise TypeError("Expected an Entry")
        self._entries[index] = entry

    def insert(self, index, entry):
        if not isinstance(entry, Entry):
            raise TypeError("Expected an Entry")
        self._entries.insert(index, entry)

    def remove(self, index):
        del self._entries[index]

    def __eq__(self, other):
        return isinstance(other, EntryCollection) and self._entries == other._entries

    def __repr__(self):
        return f"EntryCollection(count={len(self._entries)})"

    def __str__(self):
        return f"Записей: {len(self._entries)}"


class ActivityEvent(Entity):
    def __init__(self, action, details=""):
        self.action = action
        self.details = details
        self.timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = str(value)

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._action = str(value)

    @property
    def details(self):
        return self._details

    @details.setter
    def details(self, value):
        self._details = str(value)

    def identity(self):
        return self.timestamp, self.action, self.details

    def to_fields(self):
        return FieldMap(
            (
                ("timestamp", self.timestamp),
                ("action", self.action),
                ("details", self.details),
            )
        )

    def __eq__(self, other):
        return isinstance(other, ActivityEvent) and self.identity() == other.identity()

    def __repr__(self):
        return f"ActivityEvent({self.timestamp!r}, {self.action!r})"

    def __str__(self):
        return f"{self.timestamp}: {self.action}"
