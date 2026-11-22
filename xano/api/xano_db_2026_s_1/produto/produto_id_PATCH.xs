// Edit Produto record
query "produto/{produto_id}" verb=PATCH {
  api_group = "XANO_DB_2026_S1"

  input {
    int produto_id? filters=min:1
    dblink {
      table = "PRODUTO"
    }
  }

  stack {
    util.get_raw_input {
      encoding = "json"
      exclude_middleware = false
    } as $raw_input
  
    db.patch PRODUTO {
      field_name = "id"
      field_value = $input.produto_id
      data = `$input|pick:($raw_input|keys)`|filter_null|filter_empty_text
    } as $produto
  }

  response = $produto
  guid = "f8sHBcCF10wt8pRfHfwRGXKsOww"
}