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
"""ROS2 node implementation for the language learning game.

Subscribers:
    - Game state and user answers from the graphical user interface
      (GameEntryResult)

Publishers:
    - Game state and quiz questions for the game controller (GameEntry)
    - Spoken feedback for the robot (std_msgs/String)

Service Clients:
    - RagLanguageGame
        Requests personalized feedback from the Retrieval-Augmented
        Generation (RAG) service.

ROS Parameters:
    - in_game_topic (str, default='/language_learning/game/gui/state')
    - rag_service (str, default='/language_learning/rag/feedback')
    - out_topic (str, default='/qt_robot/speech/say')
    - pub_period (float, default=1.0)
    - out_game_topic (str, default='/language_learning/game/controller/state')

Description:
    This ROS 2 node coordinates the language learning game by managing the
    game state, publishing quiz questions to the game controller, and
    receiving the student's answers from the graphical user interface.
    For each submitted answer, the node sends a request to the
    RagLanguageGame service to obtain personalized feedback. The returned
    feedback is then published as text for the robot's speech synthesis
    system. The node also tracks the student's progress and score
    throughout the quiz.

Author:
    Oviya Rajavel <oviya.rajavel.inf.h-brs.de>
    Michal Stolarz <michal.stolarz@h-brs.de>
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from zat_ros2_msgs.msg import GameAnswer, GameEntry, GameEntryResult
from zat_ros2_msgs.srv import RagLanguageGame

from zat_games.quiz_config import quiz_question_lists

GAME_STATES = {1: 'IDLE', 2: 'PENDING', 3: 'STOP'}
GAME_STATES_SYMB = {GAME_STATES[key]: key for key in GAME_STATES}
QUESTION_LIST_SELECTED = False


def msg2json_game(msg):
    """Convert the message to JSON format."""
    json_data = {
        'state': GAME_STATES[msg.state],
        'questionsNum': msg.questions_total,
        'questionId': msg.id,
        'question': msg.question,
        'answerOptions': [{'type': answer.type,'content': answer.content} 
                            for answer in msg.answers],
        'answer': msg.answer,
        'result': msg.result,
        'totalResult': msg.result_final,
        'questionLists': msg.question_lists,
        'selectedQuestionList': msg.selected_question_list
    }

    return json_data


def json2msg_game(json_data):
    """Convert the JSON message to GameEntry message format."""
    msg = GameEntry()
    msg.state = GAME_STATES_SYMB[json_data['state']]
    msg.questions_total = json_data['questionsNum']
    msg.id = json_data['questionId']
    msg.question = json_data['question']
    msg.answers = [GameAnswer(type=answer['type'], 
                              content=answer['content']) 
                    for answer in json_data['answerOptions']]
    msg.answer = json_data['answer']
    msg.result = json_data['result']
    msg.result_final = json_data['totalResult']
    msg.selected_question_list = json_data['selectedQuestionList']
    msg.question_lists = json_data['questionLists']
    return msg


def msg2json_game_result(msg):
    """Convert the message to JSON format."""
    json_data = {
        'questionId': msg.id,
        'answer': msg.answer,
        'state': GAME_STATES[msg.state],
        'selectedQuestionList': msg.selected_question_list
    }
    return json_data


def json2msg_game_result(json_data):
    """Convert the JSON message to GameEntryResult message format."""
    msg = GameEntryResult()
    msg.id = json_data['questionId']
    msg.answer = json_data['answer']
    msg.state = GAME_STATES_SYMB[json_data['state']],
    msg.selected_question_list = json_data['selectedQuestionList'] 
    return msg


class UserManager:
    """Manage quiz game state and track user answers from the UI."""
    def __init__(self, config):
        """Initialize the UserManager class."""
        self._list_of_questions = config
        self._questions_num = 0
        self._quiz_questions = []
        self._questions_num = 0
        self._collected_points = 0
        self._total_points = 0
        self._game_state = GAME_STATES[1]
        self._q_id = -1
        self._ready = False
        self._selected_question_list = ""
        self._question_lists = config.keys()

    def update(self, data):
        """Update the game state."""
        if data['state'] in GAME_STATES_SYMB:
            self._game_state = data['state']
            self._selected_question_list = data['selectedQuestionList']

            if self._selected_question_list:
            
                if self._game_state == 'IDLE':
                    self._q_id = 0
                    self._collected_points = 0
                    self._ready = True
                    return

                if self._game_state == 'PENDING':
                    if data['questionId'] == -1:
                        self._q_id = 0

                    if self._q_id >= self._questions_num-1:
                        self._game_state = GAME_STATES[3]

                    if data['questionId'] == self._q_id and not self._ready:
                        self._ready = True

                        if self._q_id <= self._questions_num-1:
                            self._q_id += 1

                        if data['answer'] == 'correct':
                            self._collected_points += 1
                else:
                    return
    
    def fetch_entry(self):
        """Retrieve  the current question and answers in the game."""
        
        if self._selected_question_list:
            self._quiz_questions = self._list_of_questions[self._selected_question_list]
            self._questions_num = len(self._quiz_questions)
            self._total_points = len(self._quiz_questions)

            if self._q_id > self._questions_num-1:
                question = ""
                answers = []

            else:
                question = self._quiz_questions[self._q_id]['question']
                answers = self._quiz_questions[self._q_id]['answers']

        else:
            question = ""
            answers = []
        
        self._ready = False

        return self._q_id, question, answers, \
               self._collected_points, self._total_points, \
               self._questions_num, self._game_state, \
               self._quiz_questions, self._selected_question_list, \
               self._question_lists


class LanguageLearning(Node):
    """A ROS 2 node that manages the language learning game workflow."""
    def __init__(
            self, 
            in_game_topic: str = '/language_learning/game/gui/state',
            out_game_topic: str = '/language_learning/game/controller/state',
            out_topic='/qt_robot/speech/say',
            rag_service='/language_learning/rag/feedback',
            pub_period: float = 1.0):
        """Initialize the LanguageLearning class."""
        super().__init__('language_learning')
        self._user_manager = UserManager(quiz_question_lists)
        self._selected_question_list = ""
        self._game_gui_status = None
        self._game_controller_state = None
        self._game_gui_id = None
        self._game_controller_id = None
        self._question_list_selected = ""
        self.waiting_for_llm_response = False
        # self._server_response = str(any)

        self.declare_parameters(
            namespace='',
            parameters = [
                ('in_game_topic', in_game_topic),
                ('rag_service', rag_service),
                ('out_topic', out_topic),
                ('pub_period', pub_period)
            ])
        
        in_game_topic = self.get_parameter('in_game_topic').value
        pub_period = self.get_parameter('pub_period').value
        rag_service = self.get_parameter('rag_service').value
        out_topic = self.get_parameter('out_topic').value
        
        # game control publisher
        self._game_status_publisher = self.create_publisher(GameEntry, 
                                                            out_game_topic, 
                                                            10)
        # timer
        self._timer = self.create_timer(pub_period, self._publish_game_status)
        # game gui info subscriber
        self._game_gui_subscriber = self.create_subscription(GameEntryResult, 
                                                             in_game_topic, 
                                                             self._game_gui_callback, 
                                                             10)
        # response publisher
        self._server_response_publisher = self.create_publisher(String,
                                                                out_topic,
                                                                10)
        # Client node to access the server        
        self._client = self.create_client(RagLanguageGame, rag_service)
        while not self._client.wait_for_service(timeout_sec=2.0):
            self.get_logger().warning('RAG service server not available. Retrying to connect ...')

        self.req = RagLanguageGame.Request()

    def _game_gui_callback(self, msg):
        json_data = msg2json_game_result(msg)
        self._user_manager.update(json_data)
        
        self._game_gui_status = msg
        # Update the request object
        self._game_gui_id = msg.id
        self.req.student_answer_type = msg.answer
        self._question_list_selected = msg.selected_question_list
        # send request to the server
        self._send_request()

    def _publish_game_status(self):
        if  self.waiting_for_llm_response:
            self.get_logger().info("Waiting for LLM response", 
                                   throttle_duration_sec=2.0)
            return
    
        q_id, question, answers, points, \
        total_points, questions_num, game_state, _question_list, selected_question_list, list_of_all_questions = self._user_manager.fetch_entry()
        
        json_data = {
            'state': game_state,
            'questionsNum': questions_num,
            'questionId': q_id,
            'question': question,
            'answerOptions': answers,
            'answer': '',
            'result': points,
            'totalResult': total_points,
            'selectedQuestionList' : selected_question_list,
            'questionLists': list_of_all_questions
        }

        msg = json2msg_game(json_data)

        self._game_status_publisher.publish(msg)

        self._game_controller_state = msg
        self.get_logger().info(f"game state {json_data['state']}", throttle_duration_sec=5.0)
        self._game_controller_id = msg.id
        # Update the request object
        self.req.id = msg.id
        self.req.question = msg.question
        self.req.available_answers = msg.answers

    def _send_request(self):
        """Check for the conditions before sending a request to the server."""
        if self._game_gui_status is None:
            return
        
        if self._game_controller_state is None:
            return
        
        if self._game_controller_id != self._game_gui_status.id:
            return
        
        if not self._question_list_selected:
            return
        
        self.waiting_for_llm_response = True
        self._game_gui_status = None
        self._game_controller_state = None
        self.future = self._client.call_async(self.req)
        self.future.add_done_callback(self._handle_response)
    
    def _handle_response(self, future):
        """Handle the output from the server and publish it."""
        response = future.result()
        result = response.content
        self.waiting_for_llm_response = False
        if not result:
            return
        
        if result == "Invalid request":
            return
        
        msg = String()
        msg.data = result
        self.get_logger().info(f"LLM response: {msg}")
        self._server_response_publisher.publish(msg)
        
def main():
    """Run the LanguageLearning Node."""
    rclpy.init(args=None)
    language_game_node = LanguageLearning(
        in_game_topic='/language_learning/game/gui/state',
        out_game_topic='/language_learning/game/controller/state',
        rag_service='/language_learning/rag/feedback', 
        out_topic='/qt_robot/speech/say',
        pub_period=1.0)
    
    rclpy.spin(language_game_node)
    language_game_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
