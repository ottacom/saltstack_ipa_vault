#!/bin/bash
echo "Configuring the env"

if [ -z ${1+x} ]; then
	echo "Please enter the directory where keys are (default: /etc/salt/gpgkeys): "
	read gpg_dir
	gpg_dir="${gpg_dir:=/etc/salt/gpgkeys}"
else
	gpg_dir=$1
fi
echo "Please enter the directory where keys are (default: /saltstack_ipa_vault/_modules: "
read modules_dir
echo -n "Please enter the FreeIpa service accout that you want to use for: "
read service_account
echo -n "Please enter the password for that FreeIpa account: "
read -s service_password
echo -n "Please enter the password to encrypt/decrypt the secrets into FreeIpa vault: "
read -s decryption_key
echo -n "Please enter the password to unlock the GPG KEY : "
read -s gpg_password_key
echo -n "Please enter the directory where you want to store your secure pillar (default: /etc/salt/secure_pillar): "
read pillar_dir

echo "Your GPG key should be into this list"
echo "----"
gpg1 --homedir $gpg_dir --list-keys | grep uid |awk '{print $2}'
echo "----"
echo "Please enter the key that you want to use for free ipa module: "
read key_id
echo "Running a test"
echo -n "THIS IS A TEST" | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id" > /tmp/test.pgp
secret=$( echo -n $gpg_password_key |gpg1 --passphrase-fd 0 --batch --quiet --homedir $gpg_dir --decrypt /tmp/test.pgp)
if [ "$secret" = "THIS IS A TEST" ]; then
    echo
    echo "GPG TEST PASSED!"
else
    echo
    echo "Something went wrong during gpg test"
    exit 1
fi

gpg1 --homedir /etc/salt/gpgkeys --armor --export > /etc/salt/gpgkeys/exported_pubkey.gpg

pillar_dir="${pillar_dir:=/etc/salt/secure_pillar}"
modules_dir="${modules_dir:=/saltstack_ipa_vault/_modules}"
secret_dir="/etc/salt/ipa"
echo "Creating directory $pillar_dir"
mkdir -p $pillar_dir/ipa_secrets
chmod 0600 -R $pillar_dir

echo "Creating directory $modules_dir"
mkdir -p $modules_dir/_modules
chmod 0700 -R $modules_dir


echo "Running Kerberos test authentication"
if ! echo -n $service_password |kinit $service_account > /dev/null; then
    echo "Password problem or maybe $service_account doesn't exist in FreeIpa"
    exit 1
else
    echo "Kerberos test passed!!"
fi

mkdir $secret_dir

echo "service_account: |" > $pillar_dir/ipa_secrets/init.sls
sa=$(echo -n $service_account | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id")
echo $sa >> $pillar_dir/ipa_secrets/init.sls
echo $sa > $secret_dir/service_account

echo "service_password: |" >> $pillar_dir/ipa_secrets/init.sls
sp=$(echo -n $service_password | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id")
echo $sp >> $pillar_dir/ipa_secrets/init.sls
echo $sp > $secret_dir/service_password

echo "decryption_key: |" >> $pillar_dir/ipa_secrets/init.sls
dk=$(echo -n $decryption_key | gpg1 --homedir /etc/salt/gpgkeys --armor --batch --trust-model always --encrypt -r "$key_id")
echo $dk >> $pillar_dir/ipa_secrets/init.sls
echo $dk > $secret_dir/decryption_key
#Formatting the file
sed -i -e 's/^/     /' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     service_account: |/service_account: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     service_password: |/service_password: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
sed -i -e 's/^     decryption_key: |/decryption_key: |/' /etc/salt/secure_pillar/ipa_secrets/init.sls
cat <<EOF > $pillar_dir/top.sls
base:
  '*':
      - ipa_secrets
EOF


kinit=$(which kinit)
ipa=$(which ipa)
awk=$(which awk)
gpg1=$(which gpg1)
pyarmor=$(which pyarmor)
echo "Configuring the module..."
cp ./source/ipa_vault.py ipa_vault.py

#sed -i -e "s/to_sub_gpg_password/${gpg_password_key//\\/\\\\}/" ipa_vault.py
#sed -i -e "s/to_sub_kinit/${kinit//\//\\/}/" ipa_vault.py


sed -i -e "s/to_sub_kinit/${kinit//\//\\/}/" ipa_vault.py
sed -i -e "s/to_sub_ipa/${ipa//\//\\/}/" ipa_vault.py
sed -i -e "s/to_sub_awk/${awk//\//\\/}/" ipa_vault.py
sed -i -e "s/to_sub_gpg/${gpg//\//\\/}/" ipa_vault.py
sed -i -e "s/to_sub_gpg_home/${gpg_dir//\//\\/}/" ipa_vault.py
sed -i -e "s/to_sub_gpg_password/${gpg_password_key//\//\\/}/" ipa_vault.py

mv ipa_vault.py $modules_dir

echo "Please open the conf file /etc/salt/master and add this entries under pillar_roots area following the example below"
echo "pillar_roots:"
echo "  base:"
echo "    - /srv/pillar"
echo "    - ..."
echo "    - $pillar_dir"
echo "    - $modules_dir"

echo "Then restart salt master"
