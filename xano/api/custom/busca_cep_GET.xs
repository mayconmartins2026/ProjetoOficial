query buscaCEP verb=GET {
  api_group = "Custom"

  input {
    text cep? filters=trim
  }

  stack {
    db.query CEP {
      where = $db.CEP.cep == $input.cep
      return = {type: "list"}
    } as $CEP1
  }

  response = $CEP1
  guid = "vK60jATeeTQBWgAqBHIhSYupejo"
}