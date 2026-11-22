// Get STATUS_OE record
query "status_oe/{status_oe_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_oe_id? filters=min:1
  }

  stack {
    db.get STATUS_OE {
      field_name = "id"
      field_value = $input.status_oe_id
    } as $status_oe
  
    precondition ($status_oe != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $status_oe
  guid = "4av9nwSqqdXMc3DxL1w9c-Bf-Jg"
}