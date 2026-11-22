// Query all Status_Cliente records
query status_cliente verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query STATUS_CLIENTE {
      return = {type: "list"}
    } as $status_cliente
  }

  response = $status_cliente
  guid = "CXnbYrjMJ4fL273RNx8zzEsAcIQ"
}