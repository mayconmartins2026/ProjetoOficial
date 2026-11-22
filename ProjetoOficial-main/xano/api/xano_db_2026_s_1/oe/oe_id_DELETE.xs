// Delete OE record.
query "oe/{oe_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int oe_id? filters=min:1
  }

  stack {
    db.del OE {
      field_name = "id"
      field_value = $input.oe_id
    }
  }

  response = null
  guid = "s5drktdDx3E5MJ534d2U5rdZ-_w"
}