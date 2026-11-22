// Edit user record
query editarColaborador verb=PATCH {
  api_group = "APIsGestao"

  input {
    int user_id? filters=min:1
    dblink {
      table = "user"
      override = {password: {hidden: true, required: true}}
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch user {
      field_name = "id"
      field_value = $input.user_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
      output = [
        "id"
        "created_at"
        "name"
        "email"
        "otp_code"
        "otp_expires_at"
        "account_id"
        "role"
        "papel_id"
      ]
    } as $model
  }

  response = $model
  guid = "Mq9iYvQqF-4khH-yP-thiluXVfQ"
}