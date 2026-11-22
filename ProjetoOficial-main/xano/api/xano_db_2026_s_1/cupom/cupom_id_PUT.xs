// Update CUPOM record
query "cupom/{cupom_id}" verb=PUT {
  api_group = "XANO_DB_2026_S1"

  input {
    int cupom_id? filters=min:1
    dblink {
      table = "CUPOM"
    }
  }

  stack {
    db.edit CUPOM {
      field_name = "id"
      field_value = $input.cupom_id
      enforce_hidden_fields = false
      data = {
        nome     : $input.nome
        descricao: $input.descricao
        validade : $input.validade
        codigo   : $input.codigo
        valor    : $input.valor
      }
    } as $model
  }

  response = $model
  guid = "UpvLZbn1V0t9Ryh_tausfBC6Xwo"
}