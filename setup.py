# © 2026 Hochschule Bonn-Rhein-Sieg <https://www.h-brs.de/>
# 
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.

# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General 
# Public License for more details.

# You should have received a copy of the GNU General Public License along 
# with this program. If not, see <https://www.gnu.org/licenses/>.

import os

from setuptools import find_packages, setup

package_name = 'zat_games'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), ['launch/language_learning.py'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Michal Stolarz, Oviya Rajavel',
    maintainer_email='michal.stolarz@h-brs.de, oviya.rajavel@smail.inf.h-brs.de',
    description='Package for games controllers',
    license='GPL-3.0',
    tests_require=['pytest'],
    test_suite='test',
    entry_points={
        'console_scripts': [
            'language_learning=zat_games.language_learning:main'
        ],
    },
)
