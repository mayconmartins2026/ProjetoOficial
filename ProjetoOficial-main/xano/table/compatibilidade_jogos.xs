table compatibilidade_jogos {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text slug filters=trim|min:1
    text titulo filters=trim|min:1
    json aliases?
    text descricao filters=trim|min:1
    json generos?
    json estilos?
    int narrativa?
    int exploracao?
    int dificuldade?
    json modos?
    json plataformas?
    text url_capa?
    text cheapshark_game_id? filters=trim
    text fonte_url filters=trim|min:1
    timestamp fonte_atualizada_em?
    timestamp updated_at?=now
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "slug", op: "asc"}]}
    {type: "btree", field: [{name: "titulo", op: "asc"}]}
  ]
}
