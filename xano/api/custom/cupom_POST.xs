// Add CUPOM record
query cupom verb=POST {
  api_group = "Custom"

  input {
    dblink {
      table = "CUPOM"
    }
  }

  stack {
    db.add CUPOM {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $cupom
  }

  response = $cupom
  guid = "e0XnViURdCD6RBlRMG_LR-YFR0o"
}