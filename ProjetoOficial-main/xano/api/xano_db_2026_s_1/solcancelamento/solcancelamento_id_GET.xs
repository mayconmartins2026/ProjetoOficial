// Get SOLCANCELAMENTO record
query "solcancelamento/{solcancelamento_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int solcancelamento_id? filters=min:1
  }

  stack {
    db.get SOLCANCELAMENTO {
      field_name = "id"
      field_value = $input.solcancelamento_id
    } as $solcancelamento
  
    precondition ($solcancelamento != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $solcancelamento
  guid = "zZKduA798hVAwqZRMx4w5BrutTA"
}