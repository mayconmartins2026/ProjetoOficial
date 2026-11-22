table CUPOM {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text nome? filters=trim
    text descricao? filters=trim
    timestamp? validade?
    text codigo? filters=trim
    int valor?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "TxGTHqR6_w02VrPm9A3JRd5MDxk"
}