# simulator
* fix_server.py is the main file, it runs server.
* rule.py reads order instructions.
* action.py contains actions defined for each instruction.
* test_client.py tests server.
* sessionFix.py creates session for communitcation between server and client.
* message_factory contains messages for communication between client to server and vice versa.
* order_factory creates a python class obeject whenever server receive an order.
* twap.py is alogrithm that break large orders into small quantities linear with time.
* vwap.py is alogrithm that break large orders into small quantities non linear with time.
