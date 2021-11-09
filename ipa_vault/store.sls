ipa_vault_store_sec:
  module.run:
     - name: ipa_vault.store
     - vault_name: test123
     - secret: "Supermega!secrte#%$"
     - overwrite: True