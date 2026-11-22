query filtrarProdutos verb=GET {
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
  guid = "XhKEsDoQeG6JvZGzwgh1WB0tevs"
}