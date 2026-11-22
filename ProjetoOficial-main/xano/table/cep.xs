table CEP {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text cep? filters=trim
    text uf? filters=trim
    text cidade? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "cep", op: "asc"}]}
  ]

  tags = ["modulo 01"]
  guid = "xjGKcSPkuJzo5yuZP_drMl85xF8"
}