// Add STATUS_SOLCANCELAMENTO record
query status_solcancelamento verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "STATUS_SOLCANCELAMENTO"
    }
  }

  stack {
    db.add STATUS_SOLCANCELAMENTO {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $status_solcancelamento
  }

  response = $status_solcancelamento
  guid = "jx8ov1UxmE5HEUW-T3d7CmdPqSQ"
}