import json

from .entities import FieldMap


class JsonCodec:
    """Serialize custom mapping objects without converting them to dicts."""

    @classmethod
    def dumps(cls, value, *, indent=2):
        if indent is None:
            return cls._encode(value)
        return cls._pretty(value, indent, 0)

    @classmethod
    def _encode(cls, value):
        if isinstance(value, FieldMap):
            members = (
                f"{json.dumps(key, ensure_ascii=False)}:{cls._encode(item)}"
                for key, item in value.items()
            )
            return "{" + ",".join(members) + "}"
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(cls._encode(item) for item in value) + "]"
        return json.dumps(value, ensure_ascii=False)

    @classmethod
    def _pretty(cls, value, indent, depth):
        if isinstance(value, FieldMap):
            if not value:
                return "{}"
            pad = " " * (indent * (depth + 1))
            end_pad = " " * (indent * depth)
            members = (
                f"{pad}{json.dumps(key, ensure_ascii=False)}: "
                f"{cls._pretty(item, indent, depth + 1)}"
                for key, item in value.items()
            )
            return "{\n" + ",\n".join(members) + f"\n{end_pad}" + "}"
        if isinstance(value, (list, tuple)):
            if not value:
                return "[]"
            pad = " " * (indent * (depth + 1))
            end_pad = " " * (indent * depth)
            items = (f"{pad}{cls._pretty(item, indent, depth + 1)}" for item in value)
            return "[\n" + ",\n".join(items) + f"\n{end_pad}]"
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def loads(value):
        return json.loads(value, object_pairs_hook=FieldMap.from_pairs)
