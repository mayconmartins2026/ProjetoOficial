// Delete CUPOM record
query "cupom/{cupom_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

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
  guid = "dCTAoaVi_E1eLfWCrqfpmLZVb9U"
}