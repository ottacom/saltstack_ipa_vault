#!/bin/bash
echo "Checking prerequisites..."
kinit=$(which kinit)
if [ -z ${kinit+x} ]; then echo "Please install free ipa client and enroll this host";exit 1; else echo "- kinit installed"; fi
ipa=$(which ipa)
if [ -z ${ipa+x} ]; then echo "Please install free ipa client and enroll this host";exti 1; else echo "- ipa installed"; fi
awk=$(which awk)
if [ -z ${awk+x} ]; then echo "Please install awk";exit 1; else echo "- awk installed"; fi
salt=$(which salt)
if [ -z ${salt+x} ]; then echo "Please install salt";exit 1; else echo "- salt installed"; fi
gpg1=$(which gpg1)
if [ -z ${gpg1+x} ]; then echo "Please install gnupg1";exit 1; else echo "- gpg installed"; fi
pyarmor=$(which pyarmor)
if [ -z ${pyarmor+x} ]; then echo "Strongly reccomend to install pyarmor (pip install pyarmor) and obfuscate the module"; else echo "- pyarmor installed"; fi


echo "Please enter the directory where you want to store your gpg keys (default: /etc/salt/gpgkeys): "
read gpg_dir
gpg_dir="${gpg_dir:=/etc/salt/gpgkeys}"
echo "Creating directory /etc/salt/gpgkeys"
mkdir -p $gpg_dir
chmod 0700 $gpg_dir


echo "Please follow the instructions, remember to enter a passphrase when requested"
echo "!!! STORE YUOR PASSPHRASE IN A SAFE PLACE !!!"
echo
echo
echo "Runing: gpg1 --gen-key --homedir /etc/salt/gpgkeys"
gpg1 --gen-key --homedir /etc/salt/gpgkeys

read -p "The module installation is done, do you want proceed with the configuariton ? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
   exit 0
fi
./module_install_2.sh "$gpg_dir"