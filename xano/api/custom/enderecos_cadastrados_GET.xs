query enderecosCadastrados verb=GET {
  api_group = "Custom"

  input {
    int cliente_id? {
      table = "CLIENTE"
    }
  }

  stack {
    db.query ENDERECO {
      where = $input.cliente_id == $db.ENDERECO.cliente_id
      return = {type: "list"}
    } as $ENDERECO1
  }

  response = $ENDERECO1
  guid = "4qKGrYKbJjTVl4n_faR-sL7VO7c"
}