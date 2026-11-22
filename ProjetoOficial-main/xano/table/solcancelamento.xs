table SOLCANCELAMENTO {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text motivo? filters=trim
    int pedido_id? {
      table = "PEDIDO"
    }
  
    int status_solcancelamento_id?=1 {
      table = "STATUS_SOLCANCELAMENTO"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  tags = ["modulo 05"]
  guid = "ztbeS15ichnKr261o8zdJVUFr1c"
}