// Query all STATUS_OE records
query status_oe verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_OE {
      return = {type: "list"}
    } as $status_oe
  }

  response = $status_oe
  guid = "7F6V9Qqe6OxHv6mezD4DjqSWmZs"
}