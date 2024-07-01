#!/usr/bin/python3
import os
import subprocess
import sys
import syslog
import socket
from cryptography.fernet import Fernet

# is a pointer to the module object instance itself.
enc_fernet_key_2 ="vglmJCWSx72bcapSgPmR07rDQRNOR9c="
kinit = "/usr/bin/kinit"
ipa = "/usr/bin/ipa"
awk = "/usr/bin/awk"
gpg = "/usr/bin/gpg"
gpg_home = '/etc/salt/gpgkeys'
pillar_service_account = "/etc/salt/ipa/service_account"
pillar_service_password = "/etc/salt/ipa/service_password"
pillar_decryption_key = "/etc/salt/ipa/decryption_key"

def get_gpg_key():
    server_address = ('localhost', 8394)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        dec_info = client_socket.recv(1024).decode('utf-8')
        enc_fernet_key_1, gpg_enc_keyword = dec_info.split(",")
        enc_fernet_key = enc_fernet_key_1 + enc_fernet_key_2
        f = Fernet(enc_fernet_key.encode('utf-8'))
        decrypted_gpg_key = f.decrypt(gpg_enc_keyword.encode('utf-8'))
        return decrypted_gpg_key.decode()

def pillars():
    gpg_key = get_gpg_key()
    dec_service_account = subprocess.run(
        f"{gpg} --pinentry-mode=loopback --passphrase '{gpg_key}' --quiet --homedir '{gpg_home}' --decrypt {pillar_service_account}",
        shell=True, capture_output=True, text=True).stdout.strip()

    dec_service_password = subprocess.run(
        f"{gpg} --pinentry-mode=loopback --passphrase '{gpg_key}' --quiet --homedir '{gpg_home}' --decrypt {pillar_service_password}",
        shell=True, capture_output=True, text=True).stdout.strip()

    dec_decryption_key = subprocess.run(
        f"{gpg} --pinentry-mode=loopback --passphrase '{gpg_key}' --quiet --homedir '{gpg_home}' --decrypt {pillar_decryption_key}",
        shell=True, capture_output=True, text=True).stdout.strip()

    if not dec_service_account or not dec_service_password or not dec_decryption_key:
        syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) invalid GPG key-ID, wrong password, or something else related to GPG")
        return "Invalid GPG key-ID, wrong password, or something else related to GPG"
    else:
        return dec_service_account, dec_service_password, dec_decryption_key

def aut():
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    return_code = subprocess.run(
        f"echo -n '{dec_service_password}' | {kinit} {dec_service_account}",
        shell=True, capture_output=True).returncode
    return return_code, dec_service_account, dec_service_password, dec_decryption_key

def retrieve_shared(vault_name):
    vault_requested = vault_name
    return_code, dec_service_account, dec_service_password, dec_decryption_key = aut()
    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to decrypt {vault_requested} from freeipa vault but Kerberos credentials are invalid")
        return "Invalid Kerberos credentials or user locked"

    vault_retrieved = subprocess.run(
        f"{ipa} vault-retrieve {vault_name} --shared --password '{dec_decryption_key}' | grep Data | {awk} -F': ' '{{print $2}}' | base64 -d | xargs",
        shell=True, capture_output=True, text=True).stdout.strip()

    if not vault_retrieved:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -NOT-FOUND-(ipa vault module) request {vault_requested} but is not present in freeipa vault, try with shared")
        return "not-found"
    else:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK (ipa vault module) requested and decrypted {vault_requested} from freeipa vault")
        return vault_retrieved

def retrieve(vault_name):
    vault_requested = vault_name
    return_code, dec_service_account, dec_service_password, dec_decryption_key = aut()
    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to decrypt {vault_requested} from freeipa vault but Kerberos credentials are invalid")
        return "Invalid Kerberos credentials or user locked"

    vault_retrieved = subprocess.run(
        f"{ipa} vault-retrieve {vault_name} --password '{dec_decryption_key}' | grep Data | {awk} -F': ' '{{print $2}}' | base64 -d | xargs",
        shell=True, capture_output=True, text=True).stdout.strip()

    if not vault_retrieved:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -NOT-FOUND-(ipa vault module) request {vault_requested} but is not present in freeipa vault, try without shared")
        return "not-found"
    else:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK (ipa vault module) requested and decrypted {vault_requested} from freeipa vault")
        return vault_retrieved

def store_shared(vault_name, secret, group_member, overwrite=False):
    vault_requested = vault_name
    return_code, dec_service_account, dec_service_password, dec_decryption_key = aut()
    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa vault but Kerberos credentials are invalid")
        return "Invalid Kerberos credentials or user locked"

    secret = secret.strip()
    base64_secret = subprocess.run(
        f"echo -n '{secret}' | base64 -w 0",
        shell=True, capture_output=True, text=True).stdout.strip()

    return_code = subprocess.run(
        f"echo -n '{dec_decryption_key}' | {ipa} vault-add {vault_name} --desc {vault_name} --shared",
        shell=True, capture_output=True).returncode

    if return_code != 0 and not overwrite:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa vault but vault already exists")
        return f"-ERROR- creating vault {vault_name} already exists"
    if return_code != 0 and overwrite:
        subprocess.run(f"{ipa} vault-del {vault_name} --shared", shell=True, capture_output=True)
        return_code = subprocess.run(
            f"echo -n '{dec_decryption_key}' | {ipa} vault-add {vault_name} --desc {vault_name} --shared",
            shell=True, capture_output=True).returncode

    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong")
        return f"-ERROR- creating vault {vault_name}"

    return_code = subprocess.run(
        f"echo -n '{dec_decryption_key}' | {ipa} vault-archive {vault_name} --shared --data={base64_secret}",
        shell=True, capture_output=True).returncode

    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong during archiving")
        return f"-ERROR- during archiving {vault_name}"

    if group_member != "none":
        return_code = subprocess.run(
            f"{ipa} vault-add-member --group {group_member} {vault_name} --shared",
            shell=True, capture_output=True).returncode

        if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong adding group {group_member}")
            return f"-ERROR- adding group to {vault_name} is the group {group_member} exists?"

    validation_chksum = subprocess.run(
        f"{ipa} vault-retrieve {vault_name} --shared --password '{dec_decryption_key}' | grep Data | {awk} -F': ' '{{print $2}}' | xargs",
        shell=True, capture_output=True, text=True).stdout.strip()

    if validation_chksum == base64_secret:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK (ipa vault module) stored and encrypted {vault_name} in freeipa vault")
        return f"Vault {vault_name} stored successfully"
    else:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong during validation")
        return f"Encryption/Decryption -ERROR- on {vault_name}"

def store(vault_name, secret, overwrite=False):
    vault_requested = vault_name
    return_code, dec_service_account, dec_service_password, dec_decryption_key = aut()
    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa vault but Kerberos credentials are invalid")
        return "Invalid Kerberos credentials or user locked"

    secret = secret.strip()
    base64_secret = subprocess.run(
        f"echo -n '{secret}' | base64 -w 0",
        shell=True, capture_output=True, text=True).stdout.strip()

    return_code = subprocess.run(
        f"echo -n '{dec_decryption_key}' | {ipa} vault-add {vault_name} --desc {vault_name}",
        shell=True, capture_output=True).returncode

    if return_code != 0 and not overwrite:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa vault but vault already exists")
        return f"-ERROR- creating vault {vault_name} already exists"
    if return_code != 0 and overwrite:
        subprocess.run(f"{ipa} vault-del {vault_name}", shell=True, capture_output=True)
        return_code = subprocess.run(
            f"echo -n '{dec_decryption_key}' | {ipa} vault-add {vault_name} --desc {vault_name}",
            shell=True, capture_output=True).returncode

    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong")
        return f"-ERROR- creating vault {vault_name}"

    return_code = subprocess.run(
        f"echo -n '{dec_decryption_key}' | {ipa} vault-archive {vault_name} --data={base64_secret}",
        shell=True, capture_output=True).returncode

    if return_code != 0:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong during archiving")
        return f"-ERROR- during archiving {vault_name}"

    validation_chksum = subprocess.run(
        f"{ipa} vault-retrieve {vault_name} --password '{dec_decryption_key}' | grep Data | {awk} -F': ' '{{print $2}}' | xargs",
        shell=True, capture_output=True, text=True).stdout.strip()

    if validation_chksum == base64_secret:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK (ipa vault module) stored and encrypted {vault_name} in freeipa vault")
        return f"Vault {vault_name} stored successfully"
    else:
        syslog.syslog(syslog.LOG_INFO, f"SALT-STACK -ERROR-(ipa vault module) tried to store {vault_name} in freeipa but something went wrong during validation")
        return f"Encryption/Decryption -ERROR- on {vault_name}"

def main():
    # Testing functions
    print("Testing pillars:")
    print(pillars())
    
    print("\nTesting store:")
    print(store("example_vault", "secret"))

    print("\nTesting store_shared:")
    print(store_shared("example_shared_vault", "shared_secret", "vault_managers"))

    print("\nTesting retrieve_shared:")
    print(retrieve_shared("example_shared_vault"))

    print("\nTesting retrieve:")
    print(retrieve("example_vault"))


if __name__ == "__main__":
    main()
