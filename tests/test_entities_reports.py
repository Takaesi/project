import json
import tempfile
import unittest
from pathlib import Path

from password_manager.entities import Entry, EntryCollection, FieldMap
from password_manager.json_codec import JsonCodec
from password_manager.reports import ReportWriter, SessionReport


class EntityAndReportTests(unittest.TestCase):
    def test_entry_accessors_comparison_and_safe_repr(self):
        entry = Entry(" example.com ", " alice ", "top-secret", " note ")
        self.assertEqual(entry.site, "example.com")
        self.assertEqual(entry.login, "alice")
        self.assertEqual(entry.note, "note")
        self.assertEqual(entry, Entry("example.com", "alice", "top-secret", "note"))
        self.assertNotIn("top-secret", repr(entry))

        entry.site = "new.example"
        self.assertEqual(entry.site, "new.example")

    def test_field_map_round_trip_uses_custom_mapping(self):
        fields = FieldMap((("name", "value"), ("count", 3)))
        encoded = JsonCodec.dumps(fields)
        decoded = JsonCodec.loads(encoded)

        self.assertIsInstance(decoded, FieldMap)
        self.assertEqual(fields, decoded)
        self.assertEqual(json.loads(encoded, object_pairs_hook=FieldMap.from_pairs), fields)

    def test_report_writer_persists_session_events_as_json(self):
        report = SessionReport("2026-10-12T10:00:00+03:00")
        report.add_event("entry_added", "example.com")
        report.finish()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity_report.json"
            writer = ReportWriter(path)
            writer.write(report)
            contents = path.read_text(encoding="utf-8")
            payload = JsonCodec.loads(contents)
            self.assertNotIn("password", contents)

        self.assertEqual(payload["started_at"], "2026-10-12T10:00:00+03:00")
        self.assertEqual(payload["events"][0]["action"], "entry_added")

    def test_entry_collection_accepts_domain_objects(self):
        entries = EntryCollection((Entry("one", "a", "secret"), Entry("two", "b", "secret")))
        self.assertEqual(len(entries), 2)
        with self.assertRaises(TypeError):
            entries.add("not an entry")


if __name__ == "__main__":
    unittest.main()
