// Edit CUPOM record
query "cupom/{cupom_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int cupom_id? filters=min:1
    dblink {
      table = "CUPOM"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch CUPOM {
      field_name = "id"
      field_value = $input.cupom_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $model
  }

  response = $model
  guid = "gQiAS1-6Htfy4X1n0zmzdho5xcY"
}