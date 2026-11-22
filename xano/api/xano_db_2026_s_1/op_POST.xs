// Add OP record
query op verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "OP"
    }
  }

  stack {
    db.add OP {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $op
  }

  response = $op
  guid = "n2_Z_pQhwvmz8-GKocQ2S-EsRms"
}