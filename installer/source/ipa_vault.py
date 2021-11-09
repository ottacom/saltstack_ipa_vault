#!/usr/bin/python3
import salt
import os
import gnupg
import subprocess
import sys
import syslog

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.key="to_sub_gpg_password"
this.kinit="to_sub_kinit"
this.ipa="to_sub_ipa"
this.awk="to_sub_awk"
this.gpg = gnupg.GPG(gnupghome='to_sub_gpg_home')
this.pillar_service_account="service_account"
this.pillar_service_password="service_password"
this.pillar_decryption_key="decryption_key"


def pillars():
    service_account = __salt__['pillar.get']([pillar_service_account])
    service_password = __salt__['pillar.get']([pillar_service_password])
    decryption_key = __salt__['pillar.get']([pillar_decryption_key])
    dec_service_account = str(gpg.decrypt(service_account,passphrase=key))
    dec_service_password = str(gpg.decrypt(service_password,passphrase=key))
    dec_decryption_key = str(gpg.decrypt(decryption_key,passphrase=key))
    if dec_service_account is None and dec_service_password is None  and dec_decryption_key is None:
          syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) invalid GPG key-ID , wrong password or something else realted with GPG")
          return ( "Invalid GPG key-ID , wrong password or something else realted with GPG" )
    else:
          return dec_service_account,dec_service_password,dec_decryption_key

def aut():
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    return_code = subprocess.call("echo "+dec_service_password+" | "+ kinit +" "+dec_service_account, shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return return_code

def retrieve_shared(secret):
    secret_requested=secret
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to decrypt "+secret_requested+\
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    secret_retrieved=subprocess.Popen(ipa+" vault-retrieve "+secret+" --shared --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}' | base64 -d| xarg
s", shell=True, stdout=subprocess.PIPE).stdout.read()
    secret=(secret_retrieved.decode("utf-8"))
    if secret is None:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK -NOT-FOUND-(ipa vault module) request "+secret_requested+" but is not present\
              into freeipa vault, try with shared")
      return "not-found"
    else:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK (ipa vault module) requested and decrypted "+secret_requested+" from freeipa vault")
      return secret


def retrieve(secret):
    secret_requested=secret
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to decrypt "+secret_requested+\
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )
    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    secret_retrieved=subprocess.Popen(ipa+" vault-retrieve "+secret+" --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}' | base64 -d| xargs", shell
=True, stdout=subprocess.PIPE).stdout.read()
    secret=(secret_retrieved.decode("utf-8"))
    if secret is None:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK -NOT-FOUND-(ipa vault module) request "+secret_requested+" but is not present\
              into freeipa vault, try without shared")
      return "not-found"
    else:
      syslog.syslog(syslog.LOG_INFO, "SALT-STACK (ipa vault module) requested and decrypted "+secret_requested+" from freeipa vault")
      return secret


def store_shared(vault_name,secret,group_member,overwrite=False):
    if aut() != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " from freeipa vault but Kerberos credentials are invalid" )
            return ( "Invalid Kerberos credentials or user locked" )

    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    base64=subprocess.Popen("echo '"+secret+"' |base64", shell=True, stdout=subprocess.PIPE).stdout.read()
    base64=(base64.decode("utf-8"))
    return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL, stderr=
subprocess.DEVNULL)
    if return_code != 0 and overwrite==False:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+\
                    " into freeipa vault but Kerberos credentials are invalid" )
            return ( "-ERROR- creating vault "+vault_name+" already exists?")
    if return_code != 0 and overwrite==True:
            subprocess.call(ipa+" vault-del "+vault_name+" --shared" , shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL,
 stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- creating vault "+vault_name)
    return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-archive "+vault_name+" --shared --data="+base64, shell=True,stdout=subprocess.DEVNULL, stderr=su
bprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- during archiving "+vault_name )
    if group_member !="none":
            return_code=subprocess.call(ipa+" vault-add-member --group "+group_member+" "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVN
ULL)
            if return_code != 0:
               syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong adding group "+group_member )
               return ( "-ERROR- adding group to "+vault_name+" is the group "+group_member+" exists?" )
    validation_chksum=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --shared --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}'|xargs",shell
=True, stdout=subprocess.PIPE).stdout.read()
    validation_chksum=(validation_chksum.decode("utf-8"))
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

    dec_service_account, dec_service_password, dec_decryption_key = pillars()
    base64=subprocess.Popen("echo '"+secret+"' |base64", shell=True, stdout=subprocess.PIPE).stdout.read()
    base64=(base64.decode("utf-8"))
    return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL, stderr=
subprocess.DEVNULL)
    if return_code != 0 and overwrite==False:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+\
                    " into freeipa vault but Kerberos credentials are invalid" )
            return ( "-ERROR- creating vault "+vault_name+" already exists?")
    if return_code != 0 and overwrite==True:
            subprocess.call(ipa+" vault-del "+vault_name+" --shared" , shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-add "+vault_name+" --desc "+vault_name+" --shared",shell=True,stdout=subprocess.DEVNULL,
 stderr=subprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- creating vault "+vault_name)
    return_code=subprocess.call("echo '"+dec_decryption_key+"'|"+ipa+" vault-archive "+vault_name+" --shared --data="+base64, shell=True,stdout=subprocess.DEVNULL, stderr=su
bprocess.DEVNULL)
    if return_code != 0:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong" )
            return ( "-ERROR- during archiving "+vault_name )
    validation_chksum=subprocess.Popen(ipa+" vault-retrieve "+vault_name+" --password '"+dec_decryption_key+"' |grep Data | "+awk+" -F': ' '{print $2}'|xargs",shell=True, st
dout=subprocess.PIPE).stdout.read()
    validation_chksum=(validation_chksum.decode("utf-8"))
    if validation_chksum == base64:
            syslog.syslog("SALT-STACK (ipa vault module) stored and encrypted "+vault_name+" into freeipa vault")
            return( "Vault "+vault_name+" stored succesfully" )
    else:
            syslog.syslog(syslog.LOG_INFO, "SALT-STACK -ERROR-(ipa vault module) tried to store "+vault_name+ \
                    " into freeipa but something went wrong during the validation" )
            return ( "Encryption/Decryption -ERROR- on "+vault_name )