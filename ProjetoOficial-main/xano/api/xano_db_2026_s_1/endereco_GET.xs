// Query all Endereco records
query endereco verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
    int cliente_id? {
      table = "CLIENTE"
    }
  }

  stack {
    db.query ENDERECO {
      where = $input.cliente_id == $auth.id
      return = {type: "list"}
    } as $endereco
  }

  response = $endereco
  guid = "Obmic7QF3Iz33u4R0aJzj0aQ3ew"
}