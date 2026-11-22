// Get cartaotoknzd record
query "cartaotoknzd/{cartaotoknzd_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int cartaotoknzd_id? filters=min:1
  }

  stack {
    db.get CARTAOTOKNZD {
      field_name = "id"
      field_value = $input.cartaotoknzd_id
    } as $cartaotoknzd
  
    precondition ($cartaotoknzd != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $cartaotoknzd
  guid = "lEYAAsM24Nzdlv4D64QGtVe9IVI"
}