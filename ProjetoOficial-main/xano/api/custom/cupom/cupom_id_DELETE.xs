// Delete CUPOM record.
query "cupom/{cupom_id}" verb=DELETE {
  api_group = "Custom"

  input {
    int cupom_id? filters=min:1
  }

  stack {
    db.del CUPOM {
      field_name = "id"
      field_value = $input.cupom_id
    }
  }

  response = null
  guid = "zfQqd3uEZgAPELGPqWb_WaIiSGY"
}