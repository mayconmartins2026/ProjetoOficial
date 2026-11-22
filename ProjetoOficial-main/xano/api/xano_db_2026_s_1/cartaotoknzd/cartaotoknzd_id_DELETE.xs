// Delete cartaotoknzd record.
query "cartaotoknzd/{cartaotoknzd_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int cartaotoknzd_id? filters=min:1
  }

  stack {
    db.del CARTAOTOKNZD {
      field_name = "id"
      field_value = $input.cartaotoknzd_id
    }
  }

  response = null
  guid = "pm4ubuGwMdSqJQ10J1L2p-4C8Ls"
}