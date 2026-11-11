// Upsert the authenticated user's compatibility profile.
query "compatibilidade/preferencias" verb=PUT {
  api_group = "Authentication"
  auth = "user"

  input {
    text[] generos
    text[] estilos
    int? narrativa?
    int? exploracao?
    int? dificuldade?
    text[] modos
    text[] plataformas
  }

  stack {
    precondition (
      ($input.generos|count) <= 20 &&
      ($input.estilos|count) <= 20 &&
      ($input.modos|count) <= 10 &&
      ($input.plataformas|count) <= 10
    ) {
      error_type = "inputerror"
      error = "As listas de preferências devem conter opções válidas."
    }

    precondition (
      ($input.narrativa == null || ($input.narrativa >= 1 && $input.narrativa <= 5)) &&
      ($input.exploracao == null || ($input.exploracao >= 1 && $input.exploracao <= 5)) &&
      ($input.dificuldade == null || ($input.dificuldade >= 0 && $input.dificuldade <= 3))
    ) {
      error_type = "inputerror"
      error = "Os níveis de preferência estão fora dos limites permitidos."
    }

    db.add_or_edit "compatibilidade_preferencias" {
      field_name = "user_id"
      field_value = $auth.id
      data = {
        user_id: $auth.id
        generos: $input.generos
        estilos: $input.estilos
        narrativa: $input.narrativa
        exploracao: $input.exploracao
        dificuldade: $input.dificuldade
        modos: $input.modos
        plataformas: $input.plataformas
        updated_at: now
      }
    } as $preferencias
  }

  response = {preferencias: $preferencias}
}
