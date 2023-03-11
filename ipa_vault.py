#!/usr/bin/python3
import os
import subprocess
import sys
import syslog

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.key="+jz#eZydx5fHa,-d3dH"
this.kinit="/bin/kinit"
this.ipa="/bin/ipa"
this.awk="/bin/awk"
this.gpg="/bin/gpg"
this.gpg_home='/etc/salt/gpgkeys'
this.pillar_service_account="/etc/salt/ipa/service_account"
this.pillar_service_password="/etc/salt/ipa/service_password"
this.pillar_decryption_key="/etc/salt/ipa/decryption_key"

def pillars():
    dec_service_account=subprocess.Popen(gpg+" --pinentry-mode=loopback --passphrase '"+key+"' --quiet --homedir '"+gpg_home+"' --decrypt "+pillar_service_account,bufsize=-1,close_fds=True, shell=True, stdout=subprocess.PIPE).stdout.read()
    dec_service_password=subprocess.Popen(gpg+" --pinentry-mode=loopback --passphrase '"+key+"' --quiet --homedir '"+gpg_home+"' --decrypt "+pillar_service_password,bufsize=-1,close_fds=True, shell=True, stdout=subprocess.PIPE).stdout.read()
    dec_decryption_key=subprocess.Popen(gpg+" --pinentry-mode=loopback --passphrase '"+key+"' --quiet --homedir '"+gpg_home+"' --decrypt "+pillar_decryption_key,close_fds=True,bufsize=-1, shell=True, stdout=subprocess.PIPE).stdout.read()
    dec_service_account=dec_service_account.decode("utf-8")
    dec_service_password=dec_service_password.decode("utf-8")
    dec_decryption_key=dec_decryption_key.decode("utf-8")
    if (dec_service_account is None )  or (dec_service_password is None)  or (dec_decryption_key is None):
          syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) invalid GPG key-ID , wrong password or something else realted with GPG")
          return ( "Invalid GPG key-ID , wrong password or something else realted with GPG" )
    else:
          return dec_service_account,dec_service_password,dec_decryption_key

def aut():
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    return_code = subprocess.call("echo -n '"+dec_service_password+"' |  kinit "+dec_service_account+" >/dev/null 2>&1 ",close_fds=True,bufsize=-1, shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return return_code

def retrieve_shared(vault_name):
    vault_requested=vault_name
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to decrypt "+vault_requested+\
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    vault_retrieved=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --shared --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}' | base64 -d| xargs",close_fds=True,bufsize=-1, shell=True, stdout=subprocess.PIPE).stdout.read()
    secret=(vault_retrieved.decode("utf-8"))
    if secret is None:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK -NOT-FOUND-(ipa vault module) request "+vault_requested+" but is not present\
              into freeipa vault, try with shared")
      return "not-found"
    else:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK (ipa vault module) requested and decrypted "+vault_requested+" from freeipa vault")
      return secret.strip()


def retrieve(vault_name):
    vault_requested=vault_name
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to decrypt "+vault_requested+\
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    vault_retrieved=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}' | base64 -d| xargs",bufsize=-1,close_fds=True, shell=True, stdout=subprocess.PIPE).stdout.read()
    secret=(vault_retrieved.decode("utf-8"))
    if secret is None:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK -NOT-FOUND-(ipa vault module) request "+vault_requested+" but is not present\
              into freeipa vault, try without shared")
      return "not-found"
    else:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK (ipa vault module) requested and decrypted "+vault_requested+" from freeipa vault")
      return secret.strip()


def store_shared(vault_name,secret,group_member,overwrite=False):
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )

    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    secret=secret.strip()
    base64=subprocess.Popen("echo -n '"+secret+"' |base64 -w 0", shell=True, stdout=subprocess.PIPE).stdout.read()
    base64=(base64.decode("utf-8"))
    return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0 and overwrite==False:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+\
                    " into freeipa vault but Kerberos credentials are invalid" )
            return ( "-ERROR- creating vault "+vault_name+" already exists?")
    if return_code != 0 and overwrite==True:
            subprocess.call(ipa+" vault-del "+vault_name+" --shared" , shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",close_fds=True,bufsize=-1,shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- creating vault "+vault_name)
    return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-archive "+vault_name+" --shared --data="+base64, close_fds=True,bufsize=-1,shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- during archiving "+vault_name )
    if group_member !="none":
            return_code=subprocess.call(ipa+" vault-add-member --group "+group_member+" "+vault_name+" --shared",shell=True,close_fds=True,bufsize=-1,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if return_code != 0:
               syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong adding group "+group_member )
               return ( "-ERROR- adding group to "+vault_name+" is the group "+group_member+" exists?" )
    validation_chksum=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --shared --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}'|xargs",shell=True, stdout=subprocess.PIPE).stdout.read()
    validation_chksum=(validation_chksum.decode("utf-8"))[:-1]
    if validation_chksum == base64:
            syslog.syslog("SALT-STACK (ipa vault module) stored and encrypted "+vault_name+" into freeipa vault")
            return( "Vault "+vault_name+" stored succesfully" )
    else:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong during the validation" )
            return ( "Encryption/Decryption -ERROR- on "+vault_name )

def store(vault_name,secret,overwrite=False):
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name +\
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )
    secret=secret.strip()
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    base64=subprocess.Popen("echo -n '"+secret+"' |base64 -w 0", shell=True, stdout=subprocess.PIPE).stdout.read()
    base64=(base64.decode("utf-8"))
    return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name,shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0 and overwrite==False:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+\
                    " into freeipa vault but Kerberos credentials are invalid" )
            return ( "-ERROR- creating vault "+vault_name+" already exists?")
    if return_code != 0 and overwrite==True:
            subprocess.call(ipa+" vault-del "+vault_name , shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name,close_fds=True,bufsize=-1,shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- creating vault "+vault_name)
    return_code=subprocess.call("echo -n '"+dec_decryption_key+"'|"+ipa+" vault-archive "+vault_name+" --data="+base64,close_fds=True,bufsize=-1, shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- during archiving "+vault_name )
    validation_chksum=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}'|xargs",shell=True, stdout=subprocess.PIPE).stdout.read()
    validation_chksum=(validation_chksum.decode("utf-8"))[:-1]
    if validation_chksum == base64:
            syslog.syslog("SALT-STACK (ipa vault module) stored and encrypted "+vault_name+" into freeipa vault")
            return( "Vault "+vault_name+" stored succesfully" )
    else:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong during the validation" )
            return ( "Encryption/Decryption -ERROR- on "+vault_name )
