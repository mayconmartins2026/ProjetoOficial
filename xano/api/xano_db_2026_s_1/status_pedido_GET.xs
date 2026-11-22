// Query all status_pedido records
query status_pedido verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_PEDIDO {
      return = {type: "list"}
    } as $status_pedido
  }

  response = $status_pedido
  guid = "G626mE_mmib9BhhhgGPsoutoYl8"
}