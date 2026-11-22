// Tokens de Acesso
table tokens {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    text plataforma filters=trim
    text token filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "xxnA9KMUTqAIPdYYkVIiJhIUGRw"
}