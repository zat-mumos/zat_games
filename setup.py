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
    maintainer='Michal Stolarz',
    maintainer_email='michal.stolarz@h-brs.de',
    description='Package for games controllers',
    license='MIT',
    tests_require=['pytest'],
    test_suite='test',
    entry_points={
        'console_scripts': [
            'language_learning=zat_games.language_learning:main'
        ],
    },
)
