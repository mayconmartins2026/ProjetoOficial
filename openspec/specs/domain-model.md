Modelo de domínio # GGReviews - Modelo do Domínio (Xano)

Este documento define a estrutura de dados base de dados no Xano para a plataforma Impacta.

## 1. Entidades (Tabelas no Xano)

### 1.1. User (Utilizadores)
Armazena os dados das pessoas que utilizam a plataforma.
*   **id** (integer): Identificador único do utilizador.
*   **name** (text): Nome de exibição do utilizador.
*   **email** (text): E-mail para login.
*   **password** (password): Palavra-passe armazenada como hash pelo Xano; nunca deve ser exposta em respostas ou logs. Requer pelo menos 8 caracteres, uma letra e um número.
*   **created_at** (timestamp): Data de registo.
*   **password_reset** (object, opcional): Token de redefinição armazenado como hash, prazo de expiração e indicador de uso único.
*   **img_perfil** (image, opcional): Foto de perfil pública exibida junto às avaliações do utilizador.

### 1.2. Game (Jogos)
Armazena a identificação dos jogos obtida pela API RAWG para relacioná-los com avaliações.
*   **id** (integer): ID interno no Xano.
*   **external_api_id** (integer): O ID do jogo na API RAWG.
*   **title** (text): Nome do jogo.
*   **cover_url** (text, opcional): Link para a imagem da capa.

### 1.3. Library (Biblioteca Pessoal)
Relaciona o utilizador com os jogos que ele guardou e o estado atual.
*   **id** (integer): Identificador único.
*   **user_id** (table reference -> User): O utilizador dono do registo.
*   **game_id** (table reference -> Game): O jogo guardado.
*   **status** (text): O estado atual. Valores permitidos: `Jogando`, `Jogados`, `Quero Jogar`.
*   **updated_at** (timestamp): Última vez que o status foi alterado.

### 1.4. Avaliacoes
Guarda as avaliações criadas pelos utilizadores, seguindo a tabela `avaliacoes` do Xano.
*   **id** (integer): Identificador único.
*   **user_id** (integer, table reference -> User): O autor da avaliação.
*   **nome_jogo** (text): Nome do jogo avaliado.
*   **nota** (integer): A nota atribuída, de 1 a 5.
*   **comentario** (text): A opinião escrita pelo utilizador.
*   **created_at** (timestamp): Data em que a avaliação foi publicada.

A escala inicial da aplicação é de 1 a 5. O endpoint associa a avaliação ao ID do utilizador autenticado e registra o nome do jogo no campo `nome_jogo`.

## 2. Relacionamentos
*   Um **User** pode ter muitos itens na **Library** e muitas **Avaliacoes**.
*   A **Library** relaciona o *User* ao *Game*; **Avaliacoes** relaciona o autor ao nome do jogo.