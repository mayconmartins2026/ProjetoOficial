// Delete pedido record.
query "pedido/{pedido_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int pedido_id? filters=min:1
  }

  stack {
    db.del PEDIDO {
      field_name = "id"
      field_value = $input.pedido_id
    }
  }

  response = null
  guid = "A2LWyVCh42ndiC4xNAACW1q8E3w"
}