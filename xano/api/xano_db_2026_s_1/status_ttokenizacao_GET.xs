// Query all Status_ttokenizacao records
query status_ttokenizacao verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_TTOKENIZACAO {
      return = {type: "list"}
    } as $status_ttokenizacao
  }

  response = $status_ttokenizacao
  guid = "qZe1B-6HUB4r4CROyP27NlZsadU"
}