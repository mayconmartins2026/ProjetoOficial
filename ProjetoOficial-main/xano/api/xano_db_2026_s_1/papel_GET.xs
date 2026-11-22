// Query all Papel records
query papel verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query PAPEL {
      return = {type: "list"}
    } as $papel
  }

  response = $papel
  guid = "RlUOoCAdkDP3TWFECGzFAU9_6Z8"
}