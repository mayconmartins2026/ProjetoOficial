// Delete Status_Cliente record.
query "status_cliente/{status_cliente_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_cliente_id? filters=min:1
  }

  stack {
    db.del STATUS_CLIENTE {
      field_name = "id"
      field_value = $input.status_cliente_id
    }
  }

  response = null
  guid = "DIQctS7uVrhHA0ce72cOH1bT5O4"
}