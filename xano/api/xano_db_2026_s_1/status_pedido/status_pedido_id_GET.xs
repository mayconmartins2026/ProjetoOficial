// Get status_pedido record
query "status_pedido/{status_pedido_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_pedido_id? filters=min:1
  }

  stack {
    db.get STATUS_PEDIDO {
      field_name = "id"
      field_value = $input.status_pedido_id
    } as $status_pedido
  
    precondition ($status_pedido != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $status_pedido
  guid = "DVt_qqZFpTgE5un4gX-biamj1mE"
}