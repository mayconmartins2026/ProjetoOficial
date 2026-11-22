query novoColaborador verb=POST {
  api_group = "APIsGestao"

  input {
    text nome? filters=trim
    text email? filters=trim
    text senha? filters=trim
    text telefone? filters=trim
    text localidade? filters=trim
    int papel_id? {
      table = "PAPEL"
    }
  }

  stack {
    db.add user {
      enforce_hidden_fields = false
      data = {
        name    : $input.nome
        email   : $input.email
        password: $input.senha
        papel_id: $input.papel_id
      }
    } as $user1
  }

  response = $user1
  guid = "ufmThA5cXmXkw_Q1VqYhEjn0YGY"
}