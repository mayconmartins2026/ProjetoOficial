// Delete Status_ttokenizacao record.
query "status_ttokenizacao/{status_ttokenizacao_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int status_ttokenizacao_id? filters=min:1
  }

  stack {
    db.del STATUS_TTOKENIZACAO {
      field_name = "id"
      field_value = $input.status_ttokenizacao_id
    }
  }

  response = null
  guid = "GJAXdAENoLUeiAmWUB9HB9QtsIs"
}