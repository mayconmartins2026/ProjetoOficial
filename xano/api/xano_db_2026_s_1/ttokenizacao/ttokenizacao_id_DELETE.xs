// Delete ttokenizacao record.
query "ttokenizacao/{ttokenizacao_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int ttokenizacao_id? filters=min:1
  }

  stack {
    db.del TTOKENIZACAO {
      field_name = "id"
      field_value = $input.ttokenizacao_id
    }
  }

  response = null
  guid = "UCe3-UKrzsJ7mbErRv8OgCtTPWU"
}