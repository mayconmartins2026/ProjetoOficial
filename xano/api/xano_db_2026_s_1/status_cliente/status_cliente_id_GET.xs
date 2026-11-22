// Get Status_Cliente record
query "status_cliente/{status_cliente_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_cliente_id? filters=min:1
  }

  stack {
    db.get STATUS_CLIENTE {
      field_name = "id"
      field_value = $input.status_cliente_id
    } as $status_cliente
  
    precondition ($status_cliente != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $status_cliente
  guid = "6VWbWZ2-Ki6MdCc5Xxn8IWvuXWY"
}