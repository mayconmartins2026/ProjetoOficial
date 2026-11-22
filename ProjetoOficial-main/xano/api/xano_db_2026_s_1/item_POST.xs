// Add ITEM record
query item verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "ITEM"
    }
  }

  stack {
    db.add ITEM {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $item
  }

  response = $item
  guid = "Rg68Ij2tY-1pBkDJmNUmoewPdnE"
}