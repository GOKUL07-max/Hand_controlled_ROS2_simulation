from setuptools import find_packages, setup

package_name = 'hand_vehicle_control'

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
    description='ROS 2 hand command receiver and vehicle velocity controller',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        'hand_receiver = hand_vehicle_control.hand_command_receiver:main',

        ],
    },
)
