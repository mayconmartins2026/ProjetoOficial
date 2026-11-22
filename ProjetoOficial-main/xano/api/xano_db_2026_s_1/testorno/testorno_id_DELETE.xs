// Delete TESTORNO record.
query "testorno/{testorno_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int testorno_id? filters=min:1
  }

  stack {
    db.del TESTORNO {
      field_name = "id"
      field_value = $input.testorno_id
    }
  }

  response = null
  guid = "dclv3fu4O6JamlCK7iGQJghbvAE"
}