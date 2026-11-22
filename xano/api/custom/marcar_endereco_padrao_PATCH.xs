// Apenas deixa 1 endereço padrão por cliente
query marcarEnderecoPadrao verb=PATCH {
  api_group = "Custom"

  input {
    int endereco_id? {
      table = "ENDERECO"
    }
  }

  stack {
    db.get ENDERECO {
      field_name = "id"
      field_value = $input.endereco_id
    } as $ENDERECO1
  
    db.patch ENDERECO {
      field_name = "id"
      field_value = $input.endereco_id
      data = {padrao: true}
    } as $ENDERECO2
  
    db.query ENDERECO {
      where = $ENDERECO1.cliente_id == $db.ENDERECO.cliente_id && $ENDERECO1.id != $db.ENDERECO.id
      return = {type: "list"}
    } as $ENDERECO3
  
    array.map ($ENDERECO3) {
      by = {id: $this.id, padrao: false}
    } as $x1
  
    db.bulk.patch ENDERECO {
      items = $x1
    } as $ENDERECO4
  }

  response = {padrao: $ENDERECO2, naoPadrao: $ENDERECO4}
  guid = "X1tHBQGmv8m6MnwOV8BiXzG0BeI"
}