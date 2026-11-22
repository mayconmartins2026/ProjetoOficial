table STATUS_OE {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text status? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "status", op: "asc"}]}
  ]

  tags = ["modulo 04"]
  guid = "-0aMXIvXCitmP9oqGbuB-tzfb2Q"
}