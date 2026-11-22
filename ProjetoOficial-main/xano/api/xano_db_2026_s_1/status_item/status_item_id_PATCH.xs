// Edit STATUS_ITEM record
query "status_item/{status_item_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_item_id? filters=min:1
    dblink {
      table = "STATUS_ITEM"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch STATUS_ITEM {
      field_name = "id"
      field_value = $input.status_item_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $status_item
  }

  response = $status_item
  guid = "tYS6aCQ0pjthTQd9HYIwIvN-p48"
}