// Query all OP records
query op verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query OP {
      return = {type: "list"}
    } as $op
  }

  response = $op
  guid = "YECCyRLl5df0hPXPu13GuJyc6vU"
}