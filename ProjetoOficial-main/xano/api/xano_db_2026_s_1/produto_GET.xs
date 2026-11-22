// Query all Produto records
query produto verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query PRODUTO {
      return = {type: "list"}
    } as $produto
  }

  response = {produto: $produto}
  guid = "y4Z_crP_0CpXvdc5Xfx8xN5i9QA"
}