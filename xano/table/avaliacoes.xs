table "avaliacoes" {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "public"
    }

    int user_id? {
      table = "user"
    }

    text nome_jogo? filters=trim
    int nota?
    text comentario? filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  guid = "mqAN6fmiWabgYzt326H4Krq3KoY"
}
