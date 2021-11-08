
# Saltstack - FreeIpa Vault module integration
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/banner.drawio.png)

This module enables saltsack to manage secrets on Free Ipa vault reaching a very high grade of security combining  multiple tecnologies togheter as GPG , Free Ipa Vault, SaltStack and pyarmor

# How it works
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/Workflow.drawio.png)

When you run this module, the Salt stack master will use a secure pillar to retrieve the credentials in order to get access to FreeIPA(1)
Once the secret will be retrieved/stored into FreeIPA (2) You can continue your job as usual (3).
### Important:
***We are not going to configure PGP WITHOUT protecting the PGP key with a password like  the standard configuration  suggested from the salt-stack doc https://docs.saltproject.io/en/latest/ref/renderers/all/salt.renderers.gpg.html***

# Focused on the security
In order to decrypt the secret there are at least 6 conditions to satisfy (I guess it's good enough:-) :
1.  The Salt-stack master or minion (it depends on your setup) must be enrolled into FreeIpa
2.  You need a service account who has a view on the FreeIpa Vault 
3.  Every single secret into FreeIpa Vault is stored with a password even if you are the owner of the secret a password will be requested to use the secret
4.  The credentials stored in the pillar file are encrypted with GPG
5.  The GPG key used to encrypt the pillar (AKA secure pillar) is protected by a password
6.  The module contains the password to unlock the GPG key but the code is obfuscated by **pyarmor** we don't want to expose the Key in a flat file like something.conf



### Remind:
The module is obfuscated by **pyarmor** this is the last chance to protect the GPG PASSWORD in case someone can see the file, but  it doesn't mean that reverse engineering can't be performed on the file. 

# Things to know and best practices 

- FreeIpa module will log all the activities into SYSLOG
- Ipa module is using GPG to decode the pillar file which contains credentials to get access on FreeIpa and decode the secrets, the GPG key must be protected by a password which is hardcoded into the module, the module MUST be obfuscated usning pyarmor
- There are many ways to implement a secure env to manage secrets considering usability and security , this module can be used at least in 3 different scenarios.
- Please consider always to expose only the secrets that you really need to perform the necessary operations, using multiple service accounts is strongly recommended. 

### Scenario A (Centralized): 
Deploy this module only on the salt-stack master ONLY, running everything from the salt-stack master to retireve the secrets. You should use "orchestrate" to apply the statefile, retrieving the secret on the saltmaster and do the job on the hosts.
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/saltstack_ipa_valt.drawio.png)

### Scenario B (Half decentralized): 
Deploy the module on every minions which are enrolled into FreeIpa and able to retrieve/store the secret.
Minions are not holding the GPG KEYS so you have to decrypt and pass the info stored into the pillar (ipa service account,passowrd,password vault) from the Salt stack master to the minion, then the it will ask the secret to FreeIpa vault, again you need to "orchestrate" since multiple hosts are involved.
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/B_saltstack_ipa_valt.drawio.png)

### Scenario B (Total decentralized): 
Deploy the module and distribute the GPG KEYS on every minion who is enrolled, every single minion will be able to get the secret from FreeIPA, you don't need to "orchestrate" since no multipe host are involved, just the minion

![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/C_saltstack_ipa_valt.drawio.png)


 

# How to use it
### To retieve a secret from FreeIpa Vault
salt-call ipa_vault.retrieve  `<your secret vault stored into FreeIpa>`
```bash 
salt-call ipa_vault.retrieve root_password_vm
```
### To store a secret into FreeIpa Vault
salt-call ipa_vault.store  `<your secret vault stored into FreeIpa> <secret>`
```bash 
salt-call ipa_vault.store root_password_vm "MySup3@$sec!#et"
```
### To store a secret into FreeIpa Vault in a shared way
salt-call ipa_vault.store_shared  `<your secret vault name> <secret> <groupname(optional)>`
```bash 
salt-call ipa_vault.store root_password_vm "MySup3@$sec!#et" admin-group
```
### To store secret using state file 
store.sls
```
ipa_vault_store_sec:
  module.run:
     - name: ipa_vault.store
     - vault_name: test123
     - secret: "Supermega!secrte#%$"
     - overwrite: True
```
### To store secret using state file (shared) 
store_shared.sls
```
ipa_vault_store_sec:
  module.run:
     - name: ipa_vault.store
     - vault_name: test123
     - secret: "Supermega!secrte#%$"
     - overwrite: True
     - group_member: mygorup
```
### To retrieve secret using state file 
retrieve.sls
```
ipa_vault.retrieve:
  module.run:
     - name: ipa_vault.retrieve
     - secret: test123
```




### Software Prerequisties
- FreeIpa + Vault required (https://www.freeipa.org/page/V4/Password_Vault_2.)
- GPG Installed (Ubuntu: apt install gnupg RockyLinux,Centos,RH: yum install gnupg, yum install gnupg1 )
- Salt stack master installed (https://docs.saltproject.io/en/latest/topics/installation/index.html)
- Salt stack maste MUST be enrolled into freeipa (minions is optional)
  



### Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install foobar
```

### Usage

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

### Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

### License
[MIT](https://choosealicense.com/licenses/mit/)
