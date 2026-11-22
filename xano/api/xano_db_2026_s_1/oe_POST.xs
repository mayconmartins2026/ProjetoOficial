// Add OE record
query oe verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "OE"
    }
  }

  stack {
    db.add OE {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $oe
  }

  response = $oe
  guid = "GuwNBIMzUovE2XBvIy-CGmxcwm0"
}