// Add STATUS_ITEM record
query status_item verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "STATUS_ITEM"
    }
  }

  stack {
    db.add STATUS_ITEM {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $status_item
  }

  response = $status_item
  guid = "3eyp-F_ufn_sYxfjwNX56Sa4Ixs"
}