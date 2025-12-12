from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    game_gui_topic_arg = DeclareLaunchArgument(
        'game_gui_topic',
        default_value='/language_learning/game/gui/state',
        description='Game gui topic'
 )

    pub_period_arg = DeclareLaunchArgument(
        'pub_period',
        default_value='1.0',
        description='Period of published messages'
    )
    
    language_learning_node = Node(
        package='zat_games',
        executable='language_learning',
        name='language_learning',
        output='screen',
        parameters=[{
            'in_game_topic': LaunchConfiguration('game_gui_topic'),
            'pub_period': LaunchConfiguration('pub_period'),
        }]
    )

    return LaunchDescription([
        game_gui_topic_arg,
        pub_period_arg,
        language_learning_node
    ])