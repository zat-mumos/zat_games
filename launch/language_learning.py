# © 2026 Hochschule Bonn-Rhein-Sieg <https://www.h-brs.de/>
# 
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation, either version 3 of the License, or (at your 
# option) any later version.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General 
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program. If not, see <https://www.gnu.org/licenses/>.
"""ROS2 launch file for the language learning game.

Parameters:
    - game_gui_topic (str, default: '/language_learning/game/gui/state')
    - pub_period (float, default: 1.0)

Description:
    This launch file starts the language learning game.

Author:
    Michal Stolarz <michal.stolarz@h-brs.de>
    Oviya Rajavel <oviya.rajavel.inf.h-brs.de>
"""

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from launch import LaunchDescription


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