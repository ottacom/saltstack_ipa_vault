#!/usr/bin/python3
import socket
import sys
import os
from cryptography.fernet import Fernet
import subprocess

def main():
    key = os.environ.get('fernet_key')
    key_chunk = key[:12]
    key = os.environ.get('fernet_key').encode('utf-8')
    fernet = Fernet(key)

    # Encrypt the keyword with Fernet
    keyword = os.environ.get('keyword')
    encrypted_keyword = fernet.encrypt(keyword.encode('utf-8'))
    decode_info=(key_chunk+","+encrypted_keyword.decode('utf-8'))
    decode_info=decode_info.encode('utf-8')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8394))
    server_socket.listen(1)
    print("Server listening on port 8394...")
    
    while True:
        client_socket, address = server_socket.accept()

        # Send the encrypted keyword to the client
        client_socket.send(decode_info)
        #client_socket.send(encrypted_keyword)
        #client_socket.send(key_chunk)

        client_socket.close()

if __name__ == "__main__":
    main()
