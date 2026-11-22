// Get Cliente record
query "cliente/{cliente_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int cliente_id? filters=min:1
  }

  stack {
    db.get CLIENTE {
      field_name = "id"
      field_value = $input.cliente_id
    } as $cliente
  
    precondition ($cliente != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $cliente
  guid = "B2jwydKUX7FrefSz_5P4TG3uv6E"
}