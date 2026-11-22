// Add CUPOM record
query cupom verb=POST {
  api_group = "XANO_DB_2026_S1"

  input {
    dblink {
      table = "CUPOM"
    }
  }

  stack {
    db.add CUPOM {
      enforce_hidden_fields = false
      data = {
        created_at: "now"
        nome      : $input.nome
        descricao : $input.descricao
        validade  : $input.validade
        codigo    : $input.codigo
        valor     : $input.valor
      }
    } as $model
  }

  response = $model
  guid = "id7SZxL0lIgoz46InoHW0n4H6fQ"
}