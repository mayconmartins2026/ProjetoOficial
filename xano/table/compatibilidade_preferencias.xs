table compatibilidade_preferencias {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int user_id {
      table = "user"
    }
    json generos
    json estilos
    int? narrativa?
    int? exploracao?
    int? dificuldade?
    json modos
    json plataformas
    timestamp updated_at?=now
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "user_id", op: "asc"}]}
  ]
}
