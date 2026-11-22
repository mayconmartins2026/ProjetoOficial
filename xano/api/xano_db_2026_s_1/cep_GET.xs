// Query all CEP records
query cep verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query CEP {
      return = {type: "list"}
    } as $cep
  }

  response = $cep
  guid = "HEa8GF47BJK6T_iyORwMzScfung"
}