query "compatibilidade/catalogo" verb=GET {
  api_group = "Authentication"
  auth = "user"

  input {
    int page?=1
    int per_page?=100
  }

  stack {
    precondition ($input.page >= 1) {
      error_type = "inputerror"
      error = "A página deve ser maior que zero."
    }

    precondition ($input.per_page >= 1 && $input.per_page <= 100) {
      error_type = "inputerror"
      error = "O tamanho da página deve estar entre 1 e 100."
    }

    db.query "compatibilidade_jogos" {
      sort = {titulo: "asc"}
      return = {
        type: "list"
        paging: {
          page: $input.page
          per_page: $input.per_page
          metadata: false
        }
      }
      output = ["id", "slug", "titulo", "aliases", "descricao", "generos", "estilos", "narrativa", "exploracao", "dificuldade", "modos", "plataformas", "url_capa", "cheapshark_game_id", "fonte_url", "fonte_atualizada_em"]
    } as $jogos

    var $vocabulario {
      value = {
        generos: ["Ação", "Aventura", "RPG", "Simulação", "Estratégia", "Plataforma", "Quebra-cabeça", "Terror", "Esporte", "Corrida"]
        estilos: ["Mundo aberto", "Metroidvania", "Roguelike", "Soulslike", "Construção", "Narrativo", "Tático", "Cooperativo", "Competitivo", "Plataforma de precisão"]
        modos: ["Single-player", "Multiplayer", "Cooperativo local", "Cooperativo online"]
        plataformas: ["PC", "PlayStation", "Xbox", "Nintendo Switch"]
      }
    }
  }

  response = {jogos: $jogos, vocabulario: $vocabulario}
}
