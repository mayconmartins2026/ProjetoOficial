// Query all CUPOM records
query cupom verb=GET {
  api_group = "Custom"

  input {
  }

  stack {
    db.query CUPOM {
      return = {type: "list"}
    } as $cupom
  }

  response = $cupom
  guid = "dS7Hhd9yELkcRL1PSU4Flh2SRsI"
}