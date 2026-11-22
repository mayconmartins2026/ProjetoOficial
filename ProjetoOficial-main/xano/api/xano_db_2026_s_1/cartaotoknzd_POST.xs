// Add cartaotoknzd record
query cartaotoknzd verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "CARTAOTOKNZD"
    }
  }

  stack {
    db.add CARTAOTOKNZD {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $cartaotoknzd
  }

  response = $cartaotoknzd
  guid = "VZgGUQ81KH1gm9wq44Sbedm94yQ"
}