// Get Papel record
query "papel/{papel_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int papel_id? filters=min:1
  }

  stack {
    db.get PAPEL {
      field_name = "id"
      field_value = $input.papel_id
    } as $papel
  
    precondition ($papel != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $papel
  guid = "5xqaD9_7FMBPeDGEZEngk1iiMpw"
}