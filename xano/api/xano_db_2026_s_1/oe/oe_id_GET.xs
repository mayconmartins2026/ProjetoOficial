// Get OE record
query "oe/{oe_id}" verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int oe_id? filters=min:1
  }

  stack {
    db.get OE {
      field_name = "id"
      field_value = $input.oe_id
    } as $oe
  
    precondition ($oe != null) {
      error_type = "notfound"
      error = "Not Found."
    }
  }

  response = $oe
  guid = "fgFZfZqlvUl1IjSjV4dpEB2RAmU"
}