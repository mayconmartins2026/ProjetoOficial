// Get the user record belonging to the authentication token
query "auth/me" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    // Get the user record based on the auth ID
    db.get user {
      field_name = "id"
      field_value = $auth.id
      output = ["id", "created_at", "name", "email", "account_id", "role", "img_perfil"]
    } as $user

    function.run "Getting Started Template/create_event_log" {
      input = {
        user_id   : $user.id
        account_id: $user.account_id
        action    : "get_auth_user"
        metadata  : {
          id        : $user.id
          created_at: $user.created_at
          name      : $user.name
          email     : $user.email
          account_id: $user.account_id
          role      : $user.role
        }
      }
    } as $event_log
  
  }

  response = $user
  tags = ["xano:quick-start"]
  guid = "R_7_R-8SS4-WfM3GS4ieMO0_vls"
}