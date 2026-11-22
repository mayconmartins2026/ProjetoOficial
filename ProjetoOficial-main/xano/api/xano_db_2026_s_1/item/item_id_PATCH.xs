// Edit ITEM record
query "item/{item_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int item_id? filters=min:1
    dblink {
      table = "ITEM"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch ITEM {
      field_name = "id"
      field_value = $input.item_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $item
  }

  response = $item
  guid = "eHsoKBrQmlL-tgUr_lRK_5aKW-g"
}