// Delete Produto record.
query "produto/{produto_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int produto_id? filters=min:1
  }

  stack {
    db.del PRODUTO {
      field_name = "id"
      field_value = $input.produto_id
    }
  }

  response = null
  guid = "ONxM3LdybqIHtuhWMGgHwTz16Y8"
}