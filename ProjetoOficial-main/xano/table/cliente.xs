table CLIENTE {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text nome? filters=trim
    text celular? filters=trim
    text cpf? filters=trim
    int user_id? {
      table = "user"
    }
  
    int status_cliente_id? {
      table = "STATUS_CLIENTE"
    }
  
    text codigoclienteassas? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
  ]

  tags = ["modulo 01"]
  guid = "d1FkjmrjWJf8nlSW-HfqGrPDKlk"
}