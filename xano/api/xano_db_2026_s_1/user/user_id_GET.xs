// Get User record
query "user/{user_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int user_id? filters=min:1
  }

  stack {
    db.get "" {
      field_name = "id"
      field_value = $input.user_id
    } as $user
  
    precondition ($user != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $user
  guid = "utz2-Jg7e3v3BvBdNwM81aBU3jM"
}