query buscaCategoria verb=GET {
  api_group = "Custom"

  input {
    text categoria? filters=trim
  }

  stack {
    db.query PRODUTO {
      where = $db.PRODUTO.categoria includes $input.categoria
      return = {type: "list"}
    } as $PRODUTO1
  }

  response = $PRODUTO1
  guid = "bbH5Zi_h62w3QFfU9x1yNPTkI8E"
}