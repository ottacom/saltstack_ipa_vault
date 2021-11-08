
# Saltstack - FreeIpa Vault module integration
This module enables saltsack to retieve secrets from Free Ipa vault

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


# How it works
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/Workflow.drawio.png)

When you run this module, the Salt stack master will use a secure pillar to retrieve the credentials in order to get access to FreeIPA(1)
Once the secret will be retrieved/stored into FreeIPA (2) You can continue your job as usual (3).

# Security inforamtions
So in order to decrypt the secret there are some:-) conditions to sotisfy:
- The Salt-stack master or minion (it depends from your setup) must me enrolled into FreeIpa
- You need a service account which has a view on the FreeIpa Vault
- Every single secret into FreeIpa Vault is stored with a password
- The credetntials stored into the pillar file are encrypted with GPG
- The GPG key used to encrypt the pillar (AKA secure pillar) is protected by a password
- The module is obfuscated by pyarmor
I guess is good enough


Good to know:
- FreeIpa module will log all the activities into SYSLOG
- Some best practices: 
    Scenario A: Deploy this module only on the salt-stack master, running everything from the salt-stack master to manage the secrets. You should use "orchestrate" to apply the satefile, retrieving the secret on the saltmaster and do the job on the hosts
    Scenario B: Deploy this module only on eve
     of course you can also suppose to use this module on minions but remember that the minion MUST be enrolled into FreeIpa to retireve/store the secret
- Ipa module is using GPG to decode the pillar file which contains credentials to get access on FreeIpa and decode the secrets, the GPG key must be protected by a password which is hardcoded into the module, the module MUST be obfuscated usning pyarmor
- There are many ways to implement a secure env considering usability and security , this module can be used at leas
    1.





### Software Prerequisties
- FreeIpa + Vault required (https://www.freeipa.org/page/V4/Password_Vault_2.)
- GPG Installed (Ubuntu: apt install gnupg RockyLinux,Centos,RH: yum install gnupg, yum install gnupg1 )
- Salt stack master installed (https://docs.saltproject.io/en/latest/topics/installation/index.html)
- Salt stack maste MUST be enrolled into freeipa (minions is optional)
  
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/saltstack_ipa_valt.drawio.png)



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
