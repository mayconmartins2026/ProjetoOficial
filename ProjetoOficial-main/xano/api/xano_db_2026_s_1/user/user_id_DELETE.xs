// Delete User record.
query "user/{user_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int user_id? filters=min:1
  }

  stack {
    db.del "" {
      field_name = "id"
      field_value = $input.user_id
    }
  }

  response = null
  guid = "ko-RW-k5W5JpiLQcMVDk-mSkrUk"
}