// Get CUPOM record
query "cupom/{cupom_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int cupom_id? filters=min:1
  }

  stack {
    db.get CUPOM {
      field_name = "id"
      field_value = $input.cupom_id
    } as $model
  
    precondition ($model != null) {
      error_type = "notfound"
      error = "Not Found"
    }
  }

  response = $model
  guid = "CSCFHpwR9A9lMDpmI_auLp0GKmY"
}