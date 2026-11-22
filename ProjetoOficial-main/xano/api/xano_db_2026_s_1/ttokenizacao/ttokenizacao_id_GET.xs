// Get ttokenizacao record
query "ttokenizacao/{ttokenizacao_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int ttokenizacao_id? filters=min:1
  }

  stack {
    db.get TTOKENIZACAO {
      field_name = "id"
      field_value = $input.ttokenizacao_id
    } as $ttokenizacao
  
    precondition ($ttokenizacao != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $ttokenizacao
  guid = "_f4M4S9UGDMaPbxio_avipsr6oU"
}