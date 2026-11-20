import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    package_name = 'virtual_vehicle_description'

    package_path = get_package_share_directory(package_name)

    # URDF/Xacro
    xacro_file = os.path.join(
        package_path,
        'urdf',
        'vehicle.urdf.xacro'
    )

    # Gazebo world
    world_file = os.path.join(
        package_path,
        'worlds',
        'vehicle_world.world'
    )

    # Process Xacro
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True
            }
        ]
    )

    # Start Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            )
        ),
        launch_arguments={
            'world': world_file,
            'verbose': 'true'
        }.items()
    )

    # Spawn vehicle
    spawn_vehicle = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'virtual_vehicle',
            '-x', '0',
            '-y', '0',
            '-z', '0.1'
        ],
        output='screen'
    )

    return LaunchDescription([

        gazebo,

        robot_state_publisher,

        TimerAction(
            period=4.0,
            actions=[spawn_vehicle]
        )

    ])