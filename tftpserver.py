"""
- NOTE: REPLACE 'N' Below with your section, year, and lab number
- CS2911 - 011
- Fall 2021
- Lab 7 - TFTP Server
- Names:
  - Nathan Cernik
  - Ben Fouch
  - Aidan Regan

A Trivial File Transfer Protocol Server

Introduction: (Describe the lab in your own words)




Summary: (Summarize your experience with the lab, what you learned, what you liked,what you disliked, and any suggestions you have for improvement)





"""

# import modules -- not using "from socket import *" in order to selectively use items with "socket." prefix
import socket
import os
import math
import os.path

# Helpful constants used by TFTP
TFTP_PORT = 69
TFTP_BLOCK_SIZE = 512
MAX_UDP_PACKET_SIZE = 65536


def main():
    """
    Processes a single TFTP request
    """

    client_socket = socket_setup()

    print("Server is ready to receive a request")

    ####################################################
    # Your code starts here                            #
    #   Be sure to design and implement additional     #
    #   functions as needed                            #
    ####################################################
    (op_code, filename, mode, client_addr) = parse_request(client_socket)

    send_response(op_code, filename, mode, client_socket, client_addr)
    ####################################################
    # Your code ends here                              #
    ####################################################

    client_socket.close()


def get_file_block_count(filename):
    """
    Determines the number of TFTP blocks for the given file
    :param filename: THe name of the file
    :return: The number of TFTP blocks for the file or -1 if the file does not exist
    """
    try:
        # Use the OS call to get the file size
        #   This function throws an exception if the file doesn't exist
        file_size = os.stat(filename).st_size
        return math.ceil(file_size / TFTP_BLOCK_SIZE)
    except:
        return -1


def get_file_block(filename, block_number):
    """
    Get the file block data for the given file and block number
    :param filename: The name of the file to read
    :param block_number: The block number (1 based)
    :return: The data contents (as a bytes object) of the file block
    """
    file = open(filename, 'rb')
    block_byte_offset = (block_number - 1) * TFTP_BLOCK_SIZE
    file.seek(block_byte_offset)
    block_data = file.read(TFTP_BLOCK_SIZE)
    file.close()
    return block_data


def put_file_block(filename, block_data, block_number):
    """
    Writes a block of data to the given file
    :param filename: The name of the file to save the block to
    :param block_data: The bytes object containing the block data
    :param block_number: The block number (1 based)
    :return: Nothing
    """
    file = open(filename, 'wb')
    block_byte_offset = (block_number - 1) * TFTP_BLOCK_SIZE
    file.seek(block_byte_offset)
    file.write(block_data)
    file.close()


def socket_setup():
    """
    Sets up a UDP socket to listen on the TFTP port
    :return: The created socket
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', TFTP_PORT))
    return s


####################################################
# Write additional helper functions starting here  #
####################################################
def parse_request(udp_socket):
    (req_bytes, client_addr) = udp_socket.recvfrom(MAX_UDP_PACKET_SIZE)
    op_code = req_bytes[0:2]
    req_bytes = req_bytes[2:len(req_bytes)]
    remaining_data = req_bytes.split(b'\x00')
    filename = remaining_data[0]
    mode = remaining_data[1]

    filename = filename.decode("ASCII")
    filename = filename.encode("ASCII")
    mode = mode.decode("ASCII")
    mode = mode.encode("ASCII")
    op_code = int.from_bytes(op_code, 'big')

    return op_code, filename, mode, client_addr


def send_response(op_code, filename, mode, send_socket, client_addr):

    try:
        if op_code == 1:
            block_count = get_file_block_count(filename)
            if block_count == -1:
                raise FileNotFoundError
            for (i) in range(block_count):
                i += 1
                response = b'\x00\x03' + i.to_bytes(2, 'big') + get_file_block(filename, i)
                ack_num = 0
                while ack_num != i:
                    send_socket.sendto(response, client_addr)
                    print("Sending block " + str(i))
                    ack_num = parse_acknowledgement(send_socket)
                    print("Received acknowledgement " + str(ack_num))

        elif op_code == 2:
            # not required to implement
            raise NotImplementedError

        else:
            req_type = 'invalid request'
            raise AttributeError
    except FileNotFoundError:
        print('File not found.')
        error_response = b'\x00\x05\x00\x01' + b'File not found.' + b'\x00'
        send_socket.sendto(error_response, client_addr)

    except AttributeError:
        print('Invalid request.')
        error_response = b'\x00\x05\x00\x00' + b'Not defined.' + b'\x00'
        send_socket.sendto(error_response, client_addr)


def parse_acknowledgement(udp_socket):

    ack_bytes = udp_socket.recvfrom(MAX_UDP_PACKET_SIZE)[0]
    op_code = ack_bytes[0:2]
    ack_num = ack_bytes[2:4]
    return int.from_bytes(ack_num, 'big')


main()
