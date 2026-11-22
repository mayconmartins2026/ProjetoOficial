// Add Status_ttokenizacao record
query status_ttokenizacao verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "STATUS_TTOKENIZACAO"
    }
  }

  stack {
    db.add STATUS_TTOKENIZACAO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $status_ttokenizacao
  }

  response = $status_ttokenizacao
  guid = "95VngFZV59_nyC907irrmdypJK4"
}