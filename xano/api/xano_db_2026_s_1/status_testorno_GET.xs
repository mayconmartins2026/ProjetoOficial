// Query all STATUS_TESTORNO records
query status_testorno verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_TESTORNO {
      return = {type: "list"}
    } as $status_testorno
  }

  response = $status_testorno
  guid = "kHV8vflzOXEAbiuFuxkX1TcCnw8"
}