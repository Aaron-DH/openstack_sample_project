#
# Copyright 2013 eNovance <licensing@enovance.com>
# Copyright 2013 Red Hat, Inc.
#
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

from sqlalchemy import MetaData, Table, Column, Text
from sqlalchemy import Boolean, Integer, String, DateTime, Float


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    ReportFiles = Table(
        'report_files', meta,
        Column('file_id', String(255), primary_key=True, index=True),
        Column('task_id', String(255)),
        Column('task_name', String(255)),
        Column('task_type', String(255)),
        Column('task_period', String(255)),
        Column('file_path', String(255)),
        Column('file_time', DateTime),
        mysql_engine='InnoDB',
        mysql_charset='utf8')
    ReportFiles.create()


def downgrade(migrate_engine):
    pass
