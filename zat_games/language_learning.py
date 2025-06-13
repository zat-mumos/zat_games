import rclpy
from rclpy.node import Node
from zat_games.quiz_config import quiz_questions
from zat_ros2_msgs.msg import GameEntry, GameAnswer, GameEntryResult


GAME_STATES = {1: 'IDLE', 2: 'PENDING', 3: 'STOP'}
GAME_STATES_SYMB = {GAME_STATES[key]: key for key in GAME_STATES}


def msg2json_game(msg):
    json_data = {
        'state': GAME_STATES[msg.state],
        'questionsNum': msg.questions_total,
        'questionId': msg.id,
        'question': msg.question,
        'answerOptions': [{'type': answer.type,'content': answer.content} 
                            for answer in msg.answers],
        'answer': msg.answer,
        'result': msg.result,
        'totalResult': msg.result_final
    }

    return json_data


def json2msg_game(json_data):
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
    
    return msg


def msg2json_game_result(msg):
    json_data = {
        'questionId': msg.id,
        'answer': msg.answer,
    }
    return json_data


def json2msg_game_result(json_data):
    msg = GameEntryResult()
    msg.id = json_data['questionId']
    msg.answer = json_data['answer']    
    return msg


class UserManager():
    def __init__(self, config):
        self._quiz_questions = config
        self._questions_num = len(config)
        self._collected_points = 0
        self._total_points = len(config)
        self._game_state = GAME_STATES[2]
        self._q_id = -1
        self._ready = False

    def update(self, data):
        if data['questionId'] == -1:
            self._q_id = 0

        if data['questionId'] == self._q_id and not self._ready:
            self._ready = True

            if self._q_id < self._questions_num-1:
                self._q_id += 1

                if data['answer'] == 'correct':
                    self._collected_points += 1

            else:
                self._game_state = GAME_STATES[3]
    
    def fetch_entry(self):
        question = self._quiz_questions[self._q_id]['question']
        answers = self._quiz_questions[self._q_id]['answers']
        
        self._ready = False

        return self._q_id, question, answers, \
               self._collected_points, self._total_points, \
               self._questions_num, self._game_state


class LanguageLearning(Node):
    def __init__(
            self, 
            in_game_topic: str = '/language_learning/game/gui/state',
            out_game_topic: str = '/language_learning/game/controller/state',
            pub_period: float = 1.0):
         
        super().__init__('pose_estimator')

        self._user_manager = UserManager(config=quiz_questions)

        self.declare_parameters(
            namespace='',
            parameters = [
                ('in_game_topic', in_game_topic),
                ('pub_period', pub_period)
            ])
        
        in_game_topic = self.get_parameter('in_game_topic').value
        pub_period = self.get_parameter('pub_period').value
        
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

    def _game_gui_callback(self, msg):
        json_data = msg2json_game_result(msg)
        self._user_manager.update(json_data)
    
    def _publish_game_status(self):
        q_id, question, answers, points, \
        total_points, questions_num, game_state = self._user_manager.fetch_entry()
        
        json_data = {
            'state': game_state,
            'questionsNum': questions_num,
            'questionId': q_id,
            'question': question,
            'answerOptions': answers,
            'answer': '',
            'result': points,
            'totalResult': total_points
        }

        msg = json2msg_game(json_data)
        self._game_status_publisher.publish(msg)

        self.get_logger().info(f"game state {json_data['state']}", throttle_duration_sec=5.0)


def main():
    rclpy.init(args=None)
    
    language_game_node = LanguageLearning(
        in_game_topic='/language_learning/game/gui/state',
        out_game_topic='/language_learning/game/controller/state',
        pub_period=1.0)
    
    rclpy.spin(language_game_node)
    language_game_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
