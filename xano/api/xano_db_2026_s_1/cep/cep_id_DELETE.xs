// Delete CEP record.
query "cep/{cep_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int cep_id? filters=min:1
  }

  stack {
    db.del CEP {
      field_name = "id"
      field_value = $input.cep_id
    }
  }

  response = null
  guid = "hxRC-4g6_jSen4rtXmxJh9mFCag"
}