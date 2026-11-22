// Get Status_ttokenizacao record
query "status_ttokenizacao/{status_ttokenizacao_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_ttokenizacao_id? filters=min:1
  }

  stack {
    db.get STATUS_TTOKENIZACAO {
      field_name = "id"
      field_value = $input.status_ttokenizacao_id
    } as $status_ttokenizacao
  
    precondition ($status_ttokenizacao != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $status_ttokenizacao
  guid = "v0tRYxLSt-EycxJ0MK-NtaixlDc"
}