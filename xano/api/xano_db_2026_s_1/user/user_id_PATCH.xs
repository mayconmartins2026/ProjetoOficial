// Edit User record
query "user/{user_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int user_id? filters=min:1
    dblink {
      table = ""
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch "" {
      field_name = "id"
      field_value = $input.user_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $user
  }

  response = $user
  guid = "AMq93Yaej704Vx8J-r9YcnOnzcU"
}