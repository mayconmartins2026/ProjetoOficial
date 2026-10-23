// List only the authenticated user's evaluations.
query "avaliacoes/minhas" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.query "avaliacoes" {
      sort = {created_at: "desc"}
      return = {type: "list"}
      output = ["id", "created_at", "user_id", "nome_jogo", "nota", "comentario"]
    } as $avaliacoes

    var $minhas_avaliacoes {
      value = $avaliacoes|filter:$$.user_id == $auth.id
    }
  }

  response = {avaliacoes: $minhas_avaliacoes}
  guid = "LTUwaPL-kzp9wLT4rjvE-VFN9G0"
}
