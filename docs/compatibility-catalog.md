# Catálogo de compatibilidade

A tela de compatibilidade consulta diretamente o IGDB, serviço de jogos da
Twitch, usando `TWITCH_CLIENT_ID` e `TWITCH_CLIENT_SECRET` configurados no
`.env`. A integração carrega até 500 jogos populares e seus gêneros, temas,
modos, plataformas, descrição e capa. O catálogo fica em cache por seis horas.

O Xano continua responsável somente por recuperar e persistir as preferências
da conta autenticada. Os endpoints necessários são:

- `GET /compatibilidade/preferencias`
- `PUT /compatibilidade/preferencias`

O endpoint `GET /compatibilidade/catalogo` e a tabela
`compatibilidade_jogos` não são necessários para recomendações. As características
usadas no cálculo vêm dos campos retornados pelo IGDB; a aplicação não infere
narrativa, exploração ou dificuldade. Preferências antigas desses critérios
permanecem compatíveis com o perfil salvo, mas não participam da pontuação.

As opções de gêneros, temas, modos e plataformas são derivadas dos jogos
retornados pelo IGDB. Capa e descrição também vêm dessa API. A CheapShark
continua restrita às funcionalidades de ofertas e preços.

A compatibilidade é calculada com gêneros (50%), temas (30%) e modos (20%).
Plataformas selecionadas funcionam como filtro: um jogo precisa ter suporte
confirmado a pelo menos uma delas. Critérios sem dados não são tratados como
incompatibilidade; a pontuação só aparece quando a cobertura dos critérios
respondidos alcança 70%.
