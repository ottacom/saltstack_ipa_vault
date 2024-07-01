#!/usr/bin/python3
import socket
import sys
import os
from cryptography.fernet import Fernet
import subprocess

def main():
    # Generate a Fernet key
    key = Fernet.generate_key()
    fernet = Fernet(key)

    # Encrypt the keyword with Fernet
    print(key.decode())
    

if __name__ == "__main__":
    main()
