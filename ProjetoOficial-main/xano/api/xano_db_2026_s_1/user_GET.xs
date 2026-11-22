// Query all User records
query user verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query user {
      return = {type: "list"}
      output = [
        "id"
        "created_at"
        "name"
        "email"
        "password"
        "otp_code"
        "otp_expires_at"
        "account_id"
        "role"
        "papel_id"
      ]
    
      addon = [
        {
          name : "cargo"
          input: {PAPEL_id: $output.papel_id}
          as   : "_cargo"
        }
      ]
    } as $user1
  }

  response = $user1
  guid = "EfWl6xpVxIONwRpjhvY-Z0wDlhQ"
}