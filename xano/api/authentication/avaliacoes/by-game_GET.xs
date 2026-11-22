// List a game's evaluations with the author's public profile details.
query "avaliacoes/by-game" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
    text nome_jogo filters=trim|min:1|max:255
  }

  stack {
    db.query "avaliacoes" {
      sort = {created_at: "desc"}
      return = {type: "list"}
      output = ["id", "created_at", "user_id", "nome_jogo", "nota", "comentario"]
      addon = [
        {
          name : "review_author"
          input: {user_id: $output.user_id}
          as   : "_user"
        }
      ]
    } as $avaliacoes

    var $avaliacoes_do_jogo {
      value = $avaliacoes|filter:$$.nome_jogo == $input.nome_jogo
    }
  }

  response = {avaliacoes: $avaliacoes_do_jogo}
  guid = "bU_Bm-ogAPldxA6B3VqNwNcoe7A"
}
