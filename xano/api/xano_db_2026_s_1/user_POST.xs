// Add User record
query user verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = ""
    }
  }

  stack {
    db.add "" {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $user
  }

  response = $user
  guid = "mInD528gW-sj25QI-pvIgROAfoU"
}