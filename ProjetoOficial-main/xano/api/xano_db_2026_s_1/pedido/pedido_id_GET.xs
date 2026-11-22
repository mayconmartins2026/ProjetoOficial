// Get pedido record
query "pedido/{pedido_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int pedido_id? filters=min:1
  }

  stack {
    db.get PEDIDO {
      field_name = "id"
      field_value = $input.pedido_id
    } as $pedido
  
    precondition ($pedido != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $pedido
  guid = "RanQMwf3iSP2xnaPTfgIMtdHvXc"
}