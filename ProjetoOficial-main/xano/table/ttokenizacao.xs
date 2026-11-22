table TTOKENIZACAO {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int cliente_id? {
      table = "CLIENTE"
    }
  
    text? det_cartao_encript? filters=trim
    int status_ttokenizacao_id?=1 {
      table = "STATUS_TTOKENIZACAO"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  tags = ["modulo 02"]
  guid = "qURJsYZbvUQKo_0MiLEnmE9tCWM"
}