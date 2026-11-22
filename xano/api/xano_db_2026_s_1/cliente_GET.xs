// Query all Cliente records
query cliente verb=GET {
  api_group = "XANO_DB_2026_S1"
  auth = "user"

  input {
  }

  stack {
    db.query CLIENTE {
      return = {type: "list"}
    } as $cliente
  }

  response = $cliente
  guid = "VaxRFO-pYi3q5nfDttIsBJs0wjs"
}