// Delete user record
query "apagarColaborador/{user_id}" verb=DELETE {
  api_group = "APIsGestao"

  input {
    int user_id? filters=min:1
  }

  stack {
    db.del user {
      field_name = "id"
      field_value = $input.user_id
    }
  }

  response = null
  guid = "NlraJ-OwxPTFCSkHY2oB1knahJQ"
}