// Add SOLCANCELAMENTO record
query solcancelamento verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "SOLCANCELAMENTO"
    }
  }

  stack {
    db.add SOLCANCELAMENTO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $solcancelamento
  }

  response = $solcancelamento
  guid = "6itG-_y0CsA35lbhq7f_Q45FsYU"
}