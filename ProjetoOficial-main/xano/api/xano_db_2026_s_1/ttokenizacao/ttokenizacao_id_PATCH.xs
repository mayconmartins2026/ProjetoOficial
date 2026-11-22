// Edit ttokenizacao record
query "ttokenizacao/{ttokenizacao_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int ttokenizacao_id? filters=min:1
    dblink {
      table = "TTOKENIZACAO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch TTOKENIZACAO {
      field_name = "id"
      field_value = $input.ttokenizacao_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $ttokenizacao
  }

  response = $ttokenizacao
  guid = "kFud9RkpcKZKeVy0q9eX24z2GUo"
}