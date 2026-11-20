from setuptools import setup
import os
from glob import glob

package_name = 'virtual_vehicle_description'

setup(
    name=package_name,
    version='1.0.0',

    packages=[],

    data_files=[

        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),

        (
            'share/' + package_name,
            ['package.xml']
        ),

        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),

        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')
        ),

        (
            os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')
        ),

        (
            os.path.join('share', package_name, 'rviz'),
            glob('rviz/*')
        )

    ],

    install_requires=['setuptools'],

    zip_safe=True,

    maintainer='Developer',

    maintainer_email='user@example.com',

    description='ROS 2 Gazebo virtual vehicle',

    license='Apache-2.0',

    tests_require=['pytest'],

    entry_points={}
)