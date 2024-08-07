"""
You can create here your custom node clases for the flow.
New nodes should heritage from the base class RobotNode.
RobotNode is the base class for all robot nodes.
To use your custom node class you must register in the enum class Nodes.

Run function:
--------------
You can also override function run for default framework nodes.
Default implementation of run:

    def run(self, robot, *args, **kwargs):
        data = self.method(robot, *args, **kwargs)

        if self.next_node:
            self.next_node.run(robot, data)

"""

from enum import Enum
from robot_manager.nodes import *


class Nodes(Enum):
    StartNode = StartClass
    OperationNode = OperationClass
    EndNode = EndClass
    ConditionNode = ConditionClass



class Conditions(Enum):
    has_data = lambda data: True if len(data) > 0 else False
    eval_documents = lambda data: data if data in [2, 3] else 1