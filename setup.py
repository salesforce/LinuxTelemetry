#!/usr/bin/env python

from __future__ import with_statement

import os

from setuptools import setup

setup_kwargs = dict(zip_safe=0)

data_files = [
    ('/usr/share/collectd/plugins/python', ['plugins/diskstats.py',
                                            'plugins/vmstats.py',
                                            'plugins/buddyinfo.py',
                                            'plugins/zoneinfo.py',
                                            'plugins/netstats.py',
                                            'plugins/fusionio.py']),
    ('/etc/collectd.d', ['plugins/diskstats.conf',
                         'plugins/vmstats.conf',
                         'plugins/buddyinfo.conf',
                         'plugins/zoneinfo.conf',
                         'plugins/netstats.conf',
                         'plugins/fusionio.conf']),
]

setup(
    name='collectd-linuxtelemetry',
    version='0.3.1',
    url='https://git.soma.salesforce.com/SolrTelemetry/telemetry',
    author='Abdul Waheed',
    author_email='awaheed@salesforce.com',
    license='BSD 3-Clause',
    description='collectd plugins to monitor Linux system metrics',
    long_description='Collects Linux system metrics for cloud infrastructure monitoring, tuning, capacity planning, and analytics',
    packages=[],
    package_dir={'': 'plugins'},
    data_files=data_files,
    **setup_kwargs
)
