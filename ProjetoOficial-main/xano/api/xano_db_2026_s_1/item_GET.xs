// Query all ITEM records
query item verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query ITEM {
      return = {type: "list"}
    } as $item
  }

  response = $item
  guid = "z-XFxShCpFhgx1bAd8iT8D_KCNQ"
}