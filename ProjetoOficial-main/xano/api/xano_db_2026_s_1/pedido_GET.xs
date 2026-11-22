// Query all pedido records
query pedido verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query PEDIDO {
      return = {type: "list"}
    } as $pedido
  }

  response = $pedido
  guid = "mDQMOhKfIHSSqxivsrScpkMR8LA"
}