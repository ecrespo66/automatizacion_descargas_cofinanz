import time

from robot_manager.exceptions import RobotException


class BusinessException(RobotException):
    """Inherits from RobotException class.
    BusinessException is raised when the robot is doing something wrong.

    Arguments:
        robot: Robot instance
        message: Message sent to the user.
        next_action:  Next action when the exception is raised.
    """

    def __init__(self, robot, **kwargs):
        super().__init__(robot, **kwargs)

    def process_exception(self):
        """
        Overwrite the process_exception method from RobotException class.
        Write action when a Business exception occurs
        :param: None
        :return: None
        """
        # send log to robot manager console.

        # Process exception
        if self.next_action == "retry":
            self.retry(5)
        elif self.next_action == "restart":
            self.restart(3)
        elif self.next_action == "skip":
            self.skip()
        elif self.next_action == "stop":
            self.stop()
        else:
            try:
                #self.robot.data = self.robot.data.drop(0)
                #self.robot.data.reset_index(drop=True, inplace=True)
                self.go_to_node(self.next_action, self.message)
            except:
                raise Exception("Invalid next_action")


class SystemException(RobotException):
    """Inherits from RobotException class.
    SystemException is raised when the robot is doing something wrong.

    Arguments:
        robot: Robot instance
        message: Message sent to the user.
        next_action:  Next action when the exception is raised.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_exception(self):
        """Overwrite the process_exception method from RobotException class.
        Write action when a Business exception occurs
        :param: None
        :return: None"""
        # send log to robot manager console.
        # Process exception

        if self.next_action == "retry":
            try:
                time.sleep(10)
                self.retry(3)
            except Exception as e:
                self.robot.data = self.robot.data.drop(0)
                self.robot.data.reset_index(drop=True, inplace=True)
                self.robot.browser.close()
                self.robot.browser.open(url="https://ataria.ebizkaia.eus/es/mis-presentaciones")
                self.robot.app.login()
                self.go_to_node("get_client_data", "Error al obtener los documentos del cliente")
        elif self.next_action == "restart":
            self.restart(3)
        elif self.next_action == "skip":
            self.skip()
        elif self.next_action == "stop":
            self.stop()
        else:
            try:
                self.go_to_node(self.next_action, self.message)
            except:
                raise Exception("Invalid next_action")

