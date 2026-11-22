// Query all cartaotoknzd records
query cartaotoknzd verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query CARTAOTOKNZD {
      where = $db.CARTAOTOKNZD.cliente_id == $input.user_id
      return = {type: "list"}
    } as $cartaotoknzd
  }

  response = $cartaotoknzd
  guid = "BzL3iI7nHXnp-FpwrA4E06GPcyo"
}