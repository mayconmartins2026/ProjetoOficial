// Get Endereco record
query "endereco/{endereco_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int endereco_id? filters=min:1
  }

  stack {
    db.get ENDERECO {
      field_name = "id"
      field_value = $input.endereco_id
    } as $endereco
  
    precondition ($endereco != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $endereco
  guid = "88r0cwltKI5CBjn8ZCvOPK9U_pM"
}