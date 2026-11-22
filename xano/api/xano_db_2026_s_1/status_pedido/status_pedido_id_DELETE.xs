// Delete status_pedido record.
query "status_pedido/{status_pedido_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_pedido_id? filters=min:1
  }

  stack {
    db.del STATUS_PEDIDO {
      field_name = "id"
      field_value = $input.status_pedido_id
    }
  }

  response = null
  guid = "KOOaaQRoxg_mcSMo9WqBMTH8XIU"
}