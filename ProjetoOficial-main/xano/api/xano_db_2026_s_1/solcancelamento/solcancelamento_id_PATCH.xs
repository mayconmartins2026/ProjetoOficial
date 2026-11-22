// Edit SOLCANCELAMENTO record
query "solcancelamento/{solcancelamento_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int solcancelamento_id? filters=min:1
    dblink {
      table = "SOLCANCELAMENTO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch SOLCANCELAMENTO {
      field_name = "id"
      field_value = $input.solcancelamento_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $solcancelamento
  }

  response = $solcancelamento
  guid = "QG4w0N6iT5KvJ-HWq76U8dqUwwc"
}