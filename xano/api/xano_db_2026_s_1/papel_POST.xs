// Add Papel record
query papel verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "PAPEL"
    }
  }

  stack {
    db.add PAPEL {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $papel
  }

  response = $papel
  guid = "Xn4_LBIXcRUbvK_OaX_bEqWFsHM"
}