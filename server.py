import socket
import select
import re

HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234


#standard queries
questions = [
    "Choose Veg / Non Veg",
    "Choose pizza",
    "Choose size",
    "Choose toppings",
    "Choose quantity",
    "Ok. Let me take your info\nBOT > What's your name",
    "Your mobile number",
    "Your address",
    "Press ok to confirm"
]

#standard answer options
answers = [
    ["hi", "hello"],
    ["veg","non-veg"],
    ["option11", "option12", "option13", "option14"],
    ["option21", "option22"],
    ["option31", "option32"],
    ["option41", "option42", "option43"]
]

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()
sockets_list = [server_socket]

clients = {}
question_no = {}

print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        return False


#handles message sent thru bot
def send_message_bot(client_socket):

    if question_no[client_socket] is 9:
        message = "Order confirmed"
        sockets_list.remove(client_socket)
        del clients[client_socket]
        del question_no[client_socket]

    else:
        #print ("**TEST : " + str(question_no[client_socket]))
        message = questions[int(question_no[client_socket])]
        question_no[client_socket] = question_no[client_socket] + 1

    # If message is not empty - send it
    if message:

        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)

    else:
        message = input(f'Manual reply > ')
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)


#handle message sent manually
def send_message_manual(client_socket):

    message = input(f'Manual reply > ')
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)


while True:

    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:

            client_socket, client_address = server_socket.accept()

            user = receive_message(client_socket)
            if user is False:
                continue

            sockets_list.append(client_socket)

            clients[client_socket] = user
            question_no[client_socket] = 0

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
            
            message = "Hi " + user['data'].decode('utf-8') + ", welcome to pizza delivery."
            message = message.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')

          #  print("**Message header : " + message_header.decode('utf-8'))
           # print("**Message : " + message.decode('utf-8'))
            client_socket.send(message_header + message)

        else:

            # Receive message
            message = receive_message(notified_socket)

            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))

                sockets_list.remove(notified_socket)

                del clients[notified_socket]

                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            mess = message["data"].decode("utf-8")
            
            if (question_no[notified_socket] <= 5) and (mess.lower() in answers[question_no[notified_socket]]):
                send_message_bot(notified_socket)
            elif (question_no[notified_socket] <= 5):
                send_message_manual(notified_socket)
            else:
                send_message_bot(notified_socket)


    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]
