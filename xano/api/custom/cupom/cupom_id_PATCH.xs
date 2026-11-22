// Edit CUPOM record
query "cupom/{cupom_id}" verb=PATCH {
  api_group = "Custom"

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
    } as $cupom
  }

  response = $cupom
  guid = "VXGNPDUjjh0ghUwe3N25PTCmEGI"
}