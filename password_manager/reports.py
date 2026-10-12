from datetime import datetime, timezone
from pathlib import Path

from .config import REPORT_FILE
from .entities import ActivityEvent, Entity, FieldMap
from .json_codec import JsonCodec


class SessionReport(Entity):
    def __init__(self, started_at=None):
        self.started_at = started_at or self._now()
        self.ended_at = ""
        self.events = []

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    @property
    def started_at(self):
        return self._started_at

    @started_at.setter
    def started_at(self, value):
        self._started_at = str(value)

    @property
    def ended_at(self):
        return self._ended_at

    @ended_at.setter
    def ended_at(self, value):
        self._ended_at = str(value)

    @property
    def events(self):
        return tuple(self._events)

    @events.setter
    def events(self, value):
        events = list(value)
        if not all(isinstance(event, ActivityEvent) for event in events):
            raise TypeError("SessionReport events must be ActivityEvent objects")
        self._events = events

    def add_event(self, action, details=""):
        self._events.append(ActivityEvent(action, details))

    def finish(self):
        self.ended_at = self._now()

    def to_fields(self):
        return FieldMap(
            (
                ("started_at", self.started_at),
                ("ended_at", self.ended_at),
                ("events", [event.to_fields() for event in self.events]),
            )
        )

    def identity(self):
        return self.started_at, self.ended_at, self.events

    def to_json(self):
        return JsonCodec.dumps(self.to_fields())

    def __eq__(self, other):
        return isinstance(other, SessionReport) and self.identity() == other.identity()

    def __repr__(self):
        return f"SessionReport(events={len(self.events)})"

    def __str__(self):
        return f"Отчёт сессии: {len(self.events)} событий"


class ReportWriter(Entity):
    def __init__(self, path=None):
        self.path = REPORT_FILE if path is None else Path(path)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = Path(value)

    def identity(self):
        return (str(self.path),)

    def write(self, report):
        if not isinstance(report, SessionReport):
            raise TypeError("Expected a SessionReport")
        self.path.write_text(report.to_json() + "\n", encoding="utf-8")

    def __eq__(self, other):
        return isinstance(other, ReportWriter) and self.path == other.path

    def __repr__(self):
        return f"ReportWriter(path={str(self.path)!r})"

    def __str__(self):
        return f"Запись отчёта в {self.path}"
