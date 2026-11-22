// Delete ITEM record.
query "item/{item_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int item_id? filters=min:1
  }

  stack {
    db.del ITEM {
      field_name = "id"
      field_value = $input.item_id
    }
  }

  response = null
  guid = "m3LtownbPI4gU7lDt_NJBk4m8NY"
}