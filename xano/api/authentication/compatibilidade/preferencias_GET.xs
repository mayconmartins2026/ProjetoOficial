// Read only the authenticated user's compatibility profile.
query "compatibilidade/preferencias" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
  }

  stack {
    db.query "compatibilidade_preferencias" {
      where = $db.compatibilidade_preferencias.user_id == $auth.id
      return = {type: "single"}
      output = [
        "generos"
        "estilos"
        "narrativa"
        "exploracao"
        "dificuldade"
        "modos"
        "plataformas"
        "updated_at"
      ]
    } as $preferencias
  }

  response = {preferencias: $preferencias}
}
