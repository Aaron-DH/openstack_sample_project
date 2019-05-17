# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
SQLAlchemy models for Report data.
"""
import json
from datetime import datetime

import six
from sqlalchemy import (Column, String)
from sqlalchemy import Float, Boolean, Text, DateTime
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator

from report import utils


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = String

    @staticmethod
    def process_bind_param(value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    @staticmethod
    def process_result_value(value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class PreciseTimestamp(TypeDecorator):
    """Represents a timestamp precise to the microsecond."""

    impl = DateTime

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(DECIMAL(precision=20,
                                                   scale=6,
                                                   asdecimal=True))
        return self.impl

    @staticmethod
    def process_bind_param(value, dialect):
        if value is None:
            return value
        elif dialect.name == 'mysql':
            return utils.dt_to_decimal(value)
        return value

    @staticmethod
    def process_result_value(value, dialect):
        if value is None:
            return value
        elif dialect.name == 'mysql':
            return utils.decimal_to_dt(value)
        return value


class ReportBase(object):
    """Base class for Zeus Models."""
    __table_args__ = {'mysql_charset': "utf8",
                      'mysql_engine': "InnoDB"}
    __table_initialized__ = False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in six.iteritems(values):
            setattr(self, k, v)

    def to_dict(self):
        d = {}
        keys = self.__table__.columns.keys()
        for key in keys:
            d[key] = getattr(self, key)

        return d

Base = declarative_base(cls=ReportBase)


class ReportTasks(Base):
    """Report Tasks data."""
    __tablename__ = "report_tasks"

    task_id = Column(String(255), primary_key=True)
    task_name = Column(String(255))
    task_type = Column(String(255))
    task_period = Column(String(255))
    task_time = Column(String(255))
    task_content = Column(String(255))
    task_metadata = Column(String(255))
    task_createtime = Column(DateTime, default=datetime.now())
    task_updatetime = Column(DateTime, default=datetime.now())
    task_status = Column(String(255))
    task_language = Column(String(255))


class ReportFiles(Base):
    """Report Files data."""
    __tablename__ = "report_files"
    file_id = Column(String(255), primary_key=True)
    task_id = Column(String(255))
    task_name = Column(String(255))
    task_type = Column(String(255))
    task_period = Column(String(255))
    file_path = Column(String(255))
    file_time = Column(String(255), default=datetime.now())
