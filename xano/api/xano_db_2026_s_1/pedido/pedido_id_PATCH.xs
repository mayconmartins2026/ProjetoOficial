// Edit pedido record
query "pedido/{pedido_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int pedido_id? filters=min:1
    dblink {
      table = "PEDIDO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch PEDIDO {
      field_name = "id"
      field_value = $input.pedido_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $pedido
  }

  response = $pedido
  guid = "s75CnvhWwmNtQ4KSA2ZK4iQ9Q9Q"
}