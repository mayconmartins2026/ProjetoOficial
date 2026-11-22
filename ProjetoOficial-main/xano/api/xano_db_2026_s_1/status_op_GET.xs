// Query all STATUS_OP records
query status_op verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_OP {
      return = {type: "list"}
    } as $status_op
  }

  response = $status_op
  guid = "rxrOxV53-fzOoWBZVIc8lg7-z2c"
}