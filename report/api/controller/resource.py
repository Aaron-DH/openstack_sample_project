import json

from wsme import types as wtypes


class Base(wtypes.DynamicBase):
    """REST API Resource."""
    _wsme_attributes = []

    def to_dict(self):
        d = {}

        for attr in self._wsme_attributes:
            attr_val = getattr(self, attr.name)
            if not isinstance(attr_val, wtypes.UnsetType):
                d[attr.name] = attr_val

        return d

    @classmethod
    def from_dict(cls, d):
        obj = cls()
        for key, val in d.items():
            if hasattr(obj, key):
                setattr(obj, key, val)
        return obj

    def to_string(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        """WSME based implementation of __str__."""

        res = "%s [" % type(self).__name__

        first = True
        for attr in self._wsme_attributes:
            if not first:
                res += ', '
            else:
                first = False

            res += "%s='%s'" % (attr.name, getattr(self, attr.name))

        return res + "]"

    @classmethod
    def get_fields(cls):
        obj = cls()

        return [attr.name for attr in obj._wsme_attributes]


class Link(Base):
    """Web link."""

    href = wtypes.text
    target = wtypes.text

    @classmethod
    def sample(cls):
        return cls(href='http://example.com/here',
                   target='here')


