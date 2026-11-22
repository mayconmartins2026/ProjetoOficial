// Edit cartaotoknzd record
query "cartaotoknzd/{cartaotoknzd_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int cartaotoknzd_id? filters=min:1
    dblink {
      table = "CARTAOTOKNZD"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch CARTAOTOKNZD {
      field_name = "id"
      field_value = $input.cartaotoknzd_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $cartaotoknzd
  }

  response = $cartaotoknzd
  guid = "mfn-AdXv8-no1-DkkKoWAQU_1GE"
}