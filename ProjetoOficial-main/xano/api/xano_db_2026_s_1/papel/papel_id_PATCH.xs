// Edit Papel record
query "papel/{papel_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int papel_id? filters=min:1
    dblink {
      table = "PAPEL"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch PAPEL {
      field_name = "id"
      field_value = $input.papel_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $papel
  }

  response = $papel
  guid = "4umcGMMyY4hpGhn1uaogrfhyW5I"
}