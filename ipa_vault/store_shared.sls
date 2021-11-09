ipa_vault_store_sec_shared:
  module.run:
     - name: ipa_vault.store_shared
     - vault_name: test456
     - secret: "Supermega!secrte#%$"
     - group_member: admin_team
     - overwrite: True