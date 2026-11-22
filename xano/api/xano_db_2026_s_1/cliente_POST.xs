// Add Cliente record
query cliente verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "CLIENTE"
    }
  }

  stack {
    db.add CLIENTE {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $cliente
  }

  response = $cliente
  guid = "1O8Ha8IJRODxvhG7PKQDZuWSySE"
}