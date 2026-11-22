// Delete Cliente record.
query "cliente/{cliente_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int cliente_id? filters=min:1
  }

  stack {
    db.del CLIENTE {
      field_name = "id"
      field_value = $input.cliente_id
    }
  }

  response = null
  guid = "iKjvTVGP0gSgm7X9ReRIavJhH1Q"
}