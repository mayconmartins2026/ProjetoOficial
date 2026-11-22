// Edit OE record
query "oe/{oe_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int oe_id? filters=min:1
    dblink {
      table = "OE"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch OE {
      field_name = "id"
      field_value = $input.oe_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $oe
  }

  response = $oe
  guid = "7CAfcVhYjSeHg9jccrGkzbJArJo"
}