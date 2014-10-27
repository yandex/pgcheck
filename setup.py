#!/usr/bin/env python
# encoding: utf-8
#
#    Copyright (c) 2014 Yandex <https://github.com/yandex>
#    Copyright (c) 2014 Other contributors as noted in the AUTHORS file.
#
#    This is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#


from setuptools import setup

setup(
    name='pgcheck',
    version='0.1',
    author='Vladimir Borodin',
    author_email='root@simply.name',
    maintainer='Sergey Lavrinenko',
    maintainer_email='s@lavr.me',
    url='https://github.com/yandex/pgcheck',
    description="Do some admin task with postgres",
    long_description=open('README.md').read(),
    license="LGPLv3+",
    platforms=["Linux", "BSD", "MacOS"],
    include_package_data=True,
    zip_safe=False,
    packages=['pgcheck'],
    entry_points={
        'console_scripts': [
            'pgcheck = pgcheck.pgcheck:main',
        ]},
    install_requires=open('requirements.txt', 'r').read(),
)
