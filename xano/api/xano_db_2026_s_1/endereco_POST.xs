// Add Endereco record
query endereco verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "ENDERECO"
    }
  }

  stack {
    db.add ENDERECO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $endereco
  }

  response = $endereco
  guid = "SPwZQH-iku3kvQW1aomAkoFTQOw"
}