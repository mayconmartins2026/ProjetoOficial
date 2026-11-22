// Query all CUPOM records
query cupom verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query CUPOM {
      return = {type: "list"}
    } as $model
  }

  response = $model
  guid = "eeetHteOSnDVu06DaLc2DPfABsQ"
}