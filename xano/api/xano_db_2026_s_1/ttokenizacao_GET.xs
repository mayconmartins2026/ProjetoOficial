// Query all ttokenizacao records
query ttokenizacao verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query TTOKENIZACAO {
      return = {type: "list"}
    } as $ttokenizacao
  }

  response = $ttokenizacao
  guid = "kpWLIWy46mm88T0od5DqOkwiYtU"
}