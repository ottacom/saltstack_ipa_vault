
<a href="https://www.linkedin.com/in/fpans/">
<img
    alt="Linkedin"
    src="https://img.shields.io/badge/linkedin-0077B5?logo=linkedin&logoColor=white&style=for-the-badge"
/>
</a>

# Saltstack & FreeIpa Vault module integration
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/banner.drawio.png)

This module enables saltsack to manage secrets on Free Ipa vault reaching a very high grade of security combining  multiple tecnologies togheter as GPG , Free Ipa Vault, SaltStack and pyarmor

# How it works
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/Workflow.drawio.png)

When you run this module, the Salt stack master will use a secure pillar to retrieve the credentials in order to get access to FreeIPA(1)
Once the secret will be retrieved/stored into FreeIPA (2) You can continue your job as usual (3).
### Important:
***We are not going to configure PGP WITHOUT protecting the PGP key with a password like  the standard configuration  suggested from the salt-stack doc https://docs.saltproject.io/en/latest/ref/renderers/all/salt.renderers.gpg.html***

# Focus on the security
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
Minions are not holding the GPG KEYS so you have to decrypt and pass the info stored into the pillar (ipa service account,passowrd,password vault) from the Salt stack master to the minion, then it will ask the secret to FreeIpa vault, again you need to "orchestrate" since multiple hosts are involved.
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/B_saltstack_ipa_valt.drawio.png)

### Scenario C (Total decentralized): 
Deploy the module and distribute the GPG KEYS on every minion who is enrolled, every single minion will be able to get the secret from FreeIPA, you don't need to "orchestrate" since no multipe hosts are involved but just the minion

![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/C_saltstack_ipa_valt.drawio.png)



### Software Prerequisties
- Python3 
- FreeIpa + Vault required (https://www.freeipa.org/page/V4/Password_Vault_2.)
- GPG Installed (Ubuntu: apt install gnupg1 ; RockyLinux,Centos,RH: yum install gnupg, yum install gnupg1 )
- Salt stack master installed (https://docs.saltproject.io/en/latest/topics/installation/index.html)
- Salt stack MUST be enrolled into freeipa (minions is optional it depends for your scenario)
- Pyarmor https://pypi.org/project/pyarmor/  - pip3 install pyarmor


# Installation

## Automatic installation

```bash
apt install gnupg1 #Ubuntu
yum install gnupg1 #Rockylinux and friends
pip3 install pyarmor

cd ~
git clone https://github.com/ottacom/saltstack_ipa_vault
cd saltstack_ipa_vault/installer
./module_install.sh
```
Then follow the instructions.
In case you make some mistakes but the GPG key it has been created succesfully, you can also consider to start
from ./module_install_2.sh avoiding to create multiple keys
Remember to edit your /etc/salt/master as metioned by the script


Now you should distribuite the pillar and the module
```bash
salt '<name of your salt master>' saltutil.refresh_pillar
cd /saltstack_ipa_vault/_modules
salt '<name of your salt master>' saltutil.sync_all 
```
Then you can start to use the module follow the example described into How to use it section


## For experts and deep customization
If you have familiar whith SaltStack and modules , FreeIpa , PGP and python you can simply create a gpg key ***protected by a password running***
```bash
mkdir /etc/salt/gpgkeys/
chmod 0700 /etc/salt/gpgkeys/
gpg1 --gen-key --homedir /etc/salt/gpgkeys/
gpg1 --homedir /etc/salt/gpgkeys --armor --export > /etc/salt/gpgkeys/exported_pubkey.gpg
gpg --list-keys  --homedir /etc/salt/gpgkeys
#Please remember your GPG password 
```

Then open the the file source/ipa_vault.py and configure the beginning of the file in this way , deploy and install the module in the way that you prefer.

```python
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this.key="your password to unlock the the GPG key"
this.kinit="/bin/kinit"
this.ipa="/bin/ipa"
this.awk="/bin/awk"
this.gpg = gnupg.GPG(gnupghome='/etc/salt/gpgkeys')
```

Make sure that the modules is located into the directory that you prefer called "_modules" ( for example /saltstack_ipa_vault/_modules )

You can create your secure pillar in the directory that you like encrypting the 3 values with GPG
  - FreeIpa service_account
  - FreeIpa service_password
  - FreeIpa decryption_key
  
```bash
pillar_dir="/etc/salt/secure_pillar"
mkdir -p $pillar_dir/ipa_secrets
echo "service_account: |" > $pillar_dir/ipa_secrets/init.sls
echo -n $service_account | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id" >> $pillar_dir/ipa_secrets/init.sls
echo "service_password: |" >> $pillar_dir/ipa_secrets/init.sls
echo -n $service_password | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id" >> $pillar_dir/ipa_secrets/init.sls
echo "decryption_key: |" >> $pillar_dir/ipa_secrets/init.sls
echo -n $decryption_key | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id" >> $pillar_dir/ipa_secrets/init.sls
sed -i -e 's/^/     /' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     service_account: |/service_account: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     service_password: |/service_password: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     decryption_key: |/decryption_key: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
cat <<EOF > $pillar_dir/top.sls
base:
  '*':
      - ipa_secrets
EOF
```
if everything is fine you should see a pillar file like this 

```txt
service_account: |
     -----BEGIN PGP MESSAGE-----
     ......
     -----END PGP MESSAGE-----
service_password: |
     -----BEGIN PGP MESSAGE-----
     ......
     -----END PGP MESSAGE-----
decryption_key: |
     -----BEGIN PGP MESSAGE-----     
     .......
     -----END PGP MESSAGE-----
```
I'm assuming at this point that your configuration into /etc/salt/master is pointing to the right section pillar_roots ,so your file it should be someting like :

```text
pillar_roots:
  base:
    - /srv/pillar
    - ...
    - /etc/salt/secure_pillar/
    - /saltstack_ipa_vault/
```
Now you should distribuite the pillar and the module
```bash
salt '<name of your salt master>' saltutil.refresh_pillar
cd /saltstack_ipa_vault/_modules
salt '<name of your salt master>' saltutil.sync_all 
```
Then you can start to use the module follow the example described into How to use it section





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
salt-call ipa_vault.store_shared root_password_vm "MySup3@$sec!#et" admin-group
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
     - name: ipa_vault.store_shared
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
### To retrieve shared secret using state file 
retrieve_shared.sls
```
ipa_vault.retrieve_shared:
  module.run:
     - name: ipa_vault.retrieve_shared
     - secret: test123
```

## Obfuscating the module (strongly reccomended)
```bash
cd /saltstack_ipa_vault/_modules
pyarmor obfuscate ipa_vault.py
cd dist
mv * ../
salt '<name of your salt master>' saltutil.clear_cache
salt '<name of your salt master>' saltutil.sync_all
```



# Referral Link
### How to write your custom module
https://docs.saltproject.io/en/latest/ref/modules/index.html
### How to install FreeIpa
https://www.freeipa.org/page/Quick_Start_Guide
### How to install and use FreeIpa Vault 
https://www.freeipa.org/page/V4/Password_Vault_2.0
### How to create a standard PGP integration with salt stack
https://docs.saltproject.io/en/latest/ref/renderers/all/salt.renderers.gpg.html

# Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


# License
[MIT](https://choosealicense.com/licenses/mit/)