// Add ttokenizacao record
query ttokenizacao verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "TTOKENIZACAO"
    }
  }

  stack {
    db.add TTOKENIZACAO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $ttokenizacao
  }

  response = $ttokenizacao
  guid = "VBlqFHQqzbLF-c9btkaIywuQuso"
}