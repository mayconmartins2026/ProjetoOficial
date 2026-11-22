// Add CEP record
query cep verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "CEP"
    }
  }

  stack {
    db.add CEP {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $cep
  }

  response = $cep
  guid = "eN-cURwUznfQEFdNBAE9zvFXx-4"
}