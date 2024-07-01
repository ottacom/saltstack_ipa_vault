#!/bin/bash
WORKING_DIR=/saltstack_ipa_vault
echo -n "Please provide the gpg_key:" 
read -s keyword
fernet_key=$(/$WORKING_DIR/keyserver/key_init.py)
chunk_fernet_key=${fernet_key:12}
export keyword="$keyword"
export fernet_key="$fernet_key"
export chunk_fernet_key="$chunk_fernet_key"
sed -i 's/^enc_fernet_key_2 =.*$/enc_fernet_key_2 ="'${chunk_fernet_key}'"/' /saltstack_ipa_vault/_modules/ipa_vault.py
sed -i 's/^enc_fernet_key_2 =.*$/enc_fernet_key_2 ="'${chunk_fernet_key}'"/' /saltstack_ipa_vault/keyserver/test.py
pkill -9 server.py
sleep 5
nohup $WORKING_DIR/keyserver/server.py   > /dev/null & 
salt-call saltutil.sync_all saltenv=base
unset keyword
unset fernet_key
unset chunk_fernet_key

