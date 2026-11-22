// Add Produto record
query produto verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "PRODUTO"
    }
  }

  stack {
    db.add PRODUTO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $produto
  }

  response = $produto
  guid = "Ix70Dab2OWMidxg5H1z7Q_dUqeM"
}