// Add TESTORNO record
query testorno verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "TESTORNO"
    }
  }

  stack {
    db.add TESTORNO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $testorno
  }

  response = $testorno
  guid = "9hBTIjUclXr8AfPgpXRg3VXAjAs"
}