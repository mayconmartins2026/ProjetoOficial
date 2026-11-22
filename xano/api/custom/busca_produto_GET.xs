query buscaProduto verb=GET {
  api_group = "Custom"

  input {
    text input? filters=trim
  }

  stack {
    db.query PRODUTO {
      where = $db.PRODUTO.nome includes $input.input
      return = {type: "list"}
    } as $PRODUTO1
  }

  response = $PRODUTO1
  guid = "7QB_D31i4nFT2e_bio_Z6-sG61U"
}