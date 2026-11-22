// Add STATUS_OP record
query status_op verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "STATUS_OP"
    }
  }

  stack {
    db.add STATUS_OP {
      enforce_hidden_fields = false
      data = {created_at: "now"}
    } as $status_op
  }

  response = $status_op
  guid = "hPQ77h_9dSQ_sQVURMpXDa4e9Ww"
}