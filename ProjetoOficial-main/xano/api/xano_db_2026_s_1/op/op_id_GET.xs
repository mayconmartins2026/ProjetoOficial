// Get OP record
query "op/{op_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int op_id? filters=min:1
  }

  stack {
    db.get OP {
      field_name = "id"
      field_value = $input.op_id
    } as $op
  
    precondition ($op != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $op
  guid = "Qr3dgcqdVP9hY2AcuOXyfr_3oIs"
}