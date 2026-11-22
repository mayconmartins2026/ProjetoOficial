table PRODUTO {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text nome? filters=trim
    text descricao? filters=trim
    int qtd_disp?
    text url_imagem? filters=trim
    decimal preco?
    bool precisa_produzir?
    enum categoria? {
      values = ["", "01", "02", "03"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]

  tags = ["modulo 03"]
  guid = "qklmkubwDDtg2BCvI0TdxZV_JeE"
}