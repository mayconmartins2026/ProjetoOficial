// Query all TESTORNO records
query testorno verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query TESTORNO {
      return = {type: "list"}
    } as $testorno
  }

  response = $testorno
  guid = "tkP9pqx7WeHTlHvATY2PEXQh87Q"
}