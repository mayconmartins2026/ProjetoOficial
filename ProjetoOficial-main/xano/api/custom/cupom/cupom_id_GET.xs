// Get CUPOM record
query "cupom/{cupom_id}" verb=GET {
  api_group = "Custom"

  input {
    int cupom_id? filters=min:1
  }

  stack {
    db.get CUPOM {
      field_name = "id"
      field_value = $input.cupom_id
    } as $cupom
  
    precondition ($cupom != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $cupom
  guid = "v_70DxPKjhJEamwSJAMiDxX_5bU"
}