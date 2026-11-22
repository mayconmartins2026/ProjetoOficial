// Delete Papel record.
query "papel/{papel_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int papel_id? filters=min:1
  }

  stack {
    db.del PAPEL {
      field_name = "id"
      field_value = $input.papel_id
    }
  }

  response = null
  guid = "Sbe2bOTTHHsKMSINyN90ewgAlHU"
}