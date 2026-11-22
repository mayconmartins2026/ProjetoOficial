// Get STATUS_TESTORNO record
query "status_testorno/{status_testorno_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_testorno_id? filters=min:1
  }

  stack {
    db.get STATUS_TESTORNO {
      field_name = "id"
      field_value = $input.status_testorno_id
    } as $status_testorno
  
    precondition ($status_testorno != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $status_testorno
  guid = "i1KQbKEFJRUqmE8m47xB8Z-8Mbw"
}