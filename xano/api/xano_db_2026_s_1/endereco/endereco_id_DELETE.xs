// Delete Endereco record.
query "endereco/{endereco_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int endereco_id? filters=min:1
  }

  stack {
    db.del ENDERECO {
      field_name = "id"
      field_value = $input.endereco_id
    }
  }

  response = null
  guid = "DxB-xXu1ZG20rRaN4097emY2C7A"
}