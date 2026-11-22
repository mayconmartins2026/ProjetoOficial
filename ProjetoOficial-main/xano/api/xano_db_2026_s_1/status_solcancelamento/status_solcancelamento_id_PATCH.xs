// Edit STATUS_SOLCANCELAMENTO record
query "status_solcancelamento/{status_solcancelamento_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_solcancelamento_id? filters=min:1
    dblink {
      table = "STATUS_SOLCANCELAMENTO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch STATUS_SOLCANCELAMENTO {
      field_name = "id"
      field_value = $input.status_solcancelamento_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $status_solcancelamento
  }

  response = $status_solcancelamento
  guid = "22YzIGvlcuRCL-ZFsR80txAy25A"
}