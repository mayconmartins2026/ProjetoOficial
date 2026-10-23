// Create an evaluation for the authenticated user.
query avalia_es verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    text nome_jogo filters=trim|min:1|max:255
    int nota
    text comentario filters=trim|min:1|max:2000
  }

  stack {
    precondition ($input.nota >= 1 && $input.nota <= 5) {
      error_type = "inputerror"
      error = "Nota deve estar entre 1 e 5."
    }

    db.add "avaliacoes" {
      enforce_hidden_fields = false
      data = {
        user_id   : $auth.id
        nome_jogo : $input.nome_jogo
        nota      : $input.nota
        comentario: $input.comentario
      }
    } as $avaliacao
  }

  response = $avaliacao
  guid = "uKufDeTNHOqryqTnPaW3NhRva4g"
}
