from setuptools import find_packages, setup

package_name = 'hand_distance_ros'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Project Maintainers',
    maintainer_email='maintainer@example.com',
    description='RealSense and MediaPipe hand gesture publisher for ROS 2',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'hand_publisher = hand_distance_ros.hand_publisher:main',
    ],

    },
)
