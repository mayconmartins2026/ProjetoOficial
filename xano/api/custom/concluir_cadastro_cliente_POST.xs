query concluirCadastroCliente verb=POST {
  api_group = "Custom"

  input {
    text nome? filters=trim
    text cpf? filters=trim
    text email? filters=trim
    text telefone? filters=trim
    password senha? {
      sensitive = true
      visibility = "internal"
    }
  
    text cep? filters=trim
    text logradouro? filters=trim
    text bairro? filters=trim
    text numero? filters=trim
    text cidade? filters=trim
    text uf? filters=trim
    text complemento? filters=trim
    text referencia? filters=trim
  }

  stack {
    db.add CEP {
      enforce_hidden_fields = false
      data = {cep: $input.cep, uf: $input.uf, cidade: $input.cidade}
    } as $CEP1
  
    db.add ENDERECO {
      enforce_hidden_fields = false
      data = {
        cliente_id : $CEP1
        cep_id     : $CEP1.id
        logradouro : $input.logradouro
        numero     : $input.numero
        complemento: $input.complemento
        bairro     : $input.bairro
        referencia : $input.referencia
      }
    } as $ENDERECO1
  
    db.add user {
      enforce_hidden_fields = false
      data = {
        id      : $ENDERECO1.id
        name    : $input.nome
        email   : $input.email
        password: $input.senha
      }
    } as $user1
  
    db.add CLIENTE {
      enforce_hidden_fields = false
      data = {
        nome   : $input.nome
        celular: $input.telefone
        cpf    : $input.cpf
        user_id: $user1.id
      }
    } as $CLIENTE1
  }

  response = $CLIENTE1
  guid = "TGlhydDlAe59EYlrL-jPEb-VMuE"
}