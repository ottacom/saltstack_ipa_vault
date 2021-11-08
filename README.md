
# Saltstack - FreeIpa Vault module integration
This module enables saltsack to retieve secrets from Free Ipa vault

# How to use it

## To retieve a secret from FreeIpa Vault
salt-call ipa_vault.retrieve  `<your secret vault stored into FreeIpa>`
```bash 
salt-call ipa_vault.retrieve root_password_vm
```

## To store a secret into FreeIpa Vault

salt-call ipa_vault.store  `<your secret vault stored into FreeIpa> <secret>`
```bash 
salt-call ipa_vault.store root_password_vm "MySup3@$sec!#et"
```

## To store a secret into FreeIpa Vault in a shared way

salt-call ipa_vault.store_shared  `<your secret vault name> <secret> <groupname(optional)>`
```bash 
salt-call ipa_vault.store root_password_vm "MySup3@$sec!#et" admin-group
```
## To store secret using state file 
store.sls
```
ipa_vault_store_sec:
  module.run:
     - name: ipa_vault.store
     - vault_name: test123
     - secret: "Supermega!secrte#%$"
     - overwrite: True
```
## To store secret using state file (shared) 
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
## To retrieve secret using state file 
retrieve.sls
```
ipa_vault.retrieve:
  module.run:
     - name: ipa_vault.retrieve
     - secret: test123
```


# How it works
![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/Workflow.drawio.png)


## Prerequisties
- FreeIpa + Vault extension enabled
- Gpg  

![alt text](https://github.com/ottacom/saltstack_ipa_vault/blob/main/doc/saltstack_ipa_valt.drawio.png)



## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install foobar
```

## Usage

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
