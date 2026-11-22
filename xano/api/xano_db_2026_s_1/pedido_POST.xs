// Add pedido record
query pedido verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "PEDIDO"
    }
  }

  stack {
    db.add PEDIDO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $pedido
  }

  response = $pedido
  guid = "z7G1RWyTggRJ6dQoligmKk26XHw"
}