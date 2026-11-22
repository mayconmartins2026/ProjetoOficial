// Delete OP record.
query "op/{op_id}" verb=DELETE {
  api_group = "XANO_DB_2026_S1"

  input {
    int op_id? filters=min:1
  }

  stack {
    db.del OP {
      field_name = "id"
      field_value = $input.op_id
    }
  }

  response = null
  guid = "_Y6N8EPLEf0NFuVzPRyda4FZObQ"
}