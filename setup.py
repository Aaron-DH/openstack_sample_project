from setuptools import setup
"""
setup(
    name='report',
    entry_points={
        'stevedore.tests':[
            'test1 = test:test1',
            'test2 = test:test2',
        ],
        'report.api.v3.extensions':[
            'versions = report.api.openstack.compute.plugins.v3.versions:Versions',
            'samples = report.api.openstack.compute.plugins.v3.samples:Samples',
        ],
        'report.storage':[
            'log = report.storage.impl_log:Connection',
            'mongodb = report.storage.impl_mongodb:Connection',
            'mysql = report.storage.impl_sqlalchemy:Connection',
            'postgresql = report.storage.impl_sqlalchemy:Connection',
            'sqlite = report.storage.impl_sqlalchemy:Connection',
            'hbase = report.storage.impl_hbase:Connection',
            'db2 = report.storage.impl_db2:Connection',
        ],
    }
)
"""
import setuptools

setuptools.setup(
    setup_requires=['pbr>=1.3'],
    pbr=True)
