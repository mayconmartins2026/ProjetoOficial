// Edit Cliente record
query "cliente/{cliente_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int cliente_id? filters=min:1
    dblink {
      table = "CLIENTE"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch CLIENTE {
      field_name = "id"
      field_value = $input.cliente_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $cliente
  }

  response = $cliente
  guid = "rvmH19K9euTa6O6zojhZu3bcqrQ"
}