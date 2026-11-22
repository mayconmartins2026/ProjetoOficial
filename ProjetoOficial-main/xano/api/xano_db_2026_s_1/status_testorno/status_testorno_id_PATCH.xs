// Edit STATUS_TESTORNO record
query "status_testorno/{status_testorno_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_testorno_id? filters=min:1
    dblink {
      table = "STATUS_TESTORNO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch STATUS_TESTORNO {
      field_name = "id"
      field_value = $input.status_testorno_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $status_testorno
  }

  response = $status_testorno
  guid = "jDN8IVJhTJJhRc8wbo_0ThZ-Mlw"
}