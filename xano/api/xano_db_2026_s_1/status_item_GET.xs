// Query all STATUS_ITEM records
query status_item verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_ITEM {
      return = {type: "list"}
    } as $status_item
  }

  response = $status_item
  guid = "Q-DpjBuXaWZJtVLF4cI8nBeaKfQ"
}