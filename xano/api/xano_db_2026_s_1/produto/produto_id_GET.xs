// Get Produto record
query "produto/{produto_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int produto_id? filters=min:1
  }

  stack {
    db.get PRODUTO {
      field_name = "id"
      field_value = $input.produto_id
    } as $produto
  
    precondition ($produto != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $produto
  guid = "55Rf3nglPYyu5pIRE_Zb-X_8jVQ"
}