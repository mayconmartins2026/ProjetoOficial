table ENDERECO {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int cliente_id? {
      table = "CLIENTE"
    }
  
    int cep_id? {
      table = "CEP"
    }
  
    text? logradouro? filters=trim
    text numero? filters=trim
    text? complemento? filters=trim
    text bairro? filters=trim
    text? referencia? filters=trim
    bool padrao?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  tags = ["modulo 01"]
  guid = "I-wzeI7qPkB82pa-6duLxjYjwqM"
}