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
"""Unit tests for the LanguageLearning ROS2 node.

Author:
    Oviya Rajavel <oviya.rajavel.inf.h-brs.de>
    Michal Stolarz <michal.stolarz@h-brs.de>
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import rclpy
from std_msgs.msg import String
from zat_ros2_msgs.msg import GameAnswer, GameEntry

from zat_games.language_learning import (
    LanguageLearning,
    json2msg_game,
    json2msg_game_result,
    msg2json_game,
    msg2json_game_result,
)

GAME_STATES = {1: 'IDLE', 2: 'PENDING', 3: 'STOP'}
GAME_STATES_SYMB = {GAME_STATES[key]: key for key in GAME_STATES}

# sample json data for testing
json_data = {
    'state': 'IDLE',   
    'questionsNum': 5,
    'questionId': -1,
    'question': "____   heißen Sie?",
    'answerOptions': [
        {"type": "correct", "content": "Wie"},
        {"type": "wrong1", "content": "Wer"},
        {"type": "wrong2", "content": "Wem"}
    ],
    'answer': 'correct',
    'result': 1,
    'totalResult': 5
}

@pytest.fixture(scope='module', autouse=True)
def rclpy_init_shutdown():
    """Mock ros node init and shutdown."""
    rclpy.init()
    yield
    rclpy.shutdown()

# Simulated GameAnswer
def make_game_answer(type_, content):
    """Creates a mock GameAnswer instance."""
    msg = GameAnswer()
    msg.type = type_
    msg.content = content
    return msg

# Simulated GameEntry
def make_game_entry(json_data):
    """Creates a mock GameEntry instance."""
    msg = GameEntry()
    msg.id = json_data['questionId']
    msg.state = GAME_STATES_SYMB[json_data['state']]
    msg.questions_total = json_data['questionsNum']
    msg.question = json_data['question']
    msg.answer = json_data['answer']
    msg.result = json_data['result']
    msg.result_final = json_data['totalResult']
    answers=[make_game_answer(ans['type'], ans['content']) for ans in json_data['answerOptions']]
    msg.answers = answers
    return msg

def test_json2msge_conversions():
    """Test the conversion of JSON to GameEntry message."""
    msg = json2msg_game(json_data)
    assert msg.state == GAME_STATES_SYMB[json_data['state']]
    assert msg.id == json_data['questionId']
    assert msg.question == json_data['question']
    assert msg.answer == json_data['answer']
    assert msg.result == json_data['result']
    assert msg.result_final == json_data['totalResult']

def test_msg2json_conversions():
    """Test the conversion of message to JSON."""
    msg = make_game_entry(json_data)
    json_convertion = msg2json_game_result(msg)
    assert json_convertion['questionId'] == msg.id
    assert json_convertion['answer'] == msg.answer
    assert json_convertion['state'] == GAME_STATES[msg.state]  

def test_msg2json_game_conversion():
    """Test the conversion of message to JSON."""
    msg = make_game_entry(json_data)
    json_conversion = msg2json_game(msg)
    assert json_conversion['state'] == GAME_STATES[msg.state]
    assert json_conversion['questionsNum'] == msg.questions_total
    assert json_conversion['questionId'] == msg.id
    assert json_conversion['question'] == msg.question
    assert json_conversion['answer'] == msg.answer
    assert json_conversion['result'] == msg.result
    assert json_conversion['totalResult'] == msg.result_final
    expected_answer_options = [{'type': a.type, 'content': a.content}
                               for a in msg.answers]
    assert json_conversion['answerOptions'] == expected_answer_options

def test_json2msg_game_result():
    """Test the conversion of JSON message to GameEntryResult."""
    converted_msg = json2msg_game_result(json_data)
    assert converted_msg.id == json_data['questionId']
    assert converted_msg.answer == json_data['answer']
    assert converted_msg.state == GAME_STATES_SYMB[json_data['state']]

def test_handle_response_publishes():
    """Test the publisher of the server."""
    with patch.object(LanguageLearning, '__init__', lambda self: None):
        node = LanguageLearning()
        node._server_response_publisher = MagicMock()

        class FakeFuture:
            """Fake server response creation."""
            def result(self):
                """Return a fake server response."""
                return SimpleNamespace(content="Testing zat_games")

        node._handle_response(FakeFuture())

        node._server_response_publisher.publish.assert_called()
        published_msg = node._server_response_publisher.publish.call_args[0][0]
        assert isinstance(published_msg, String)
        assert published_msg.data == "Testing zat_games"
