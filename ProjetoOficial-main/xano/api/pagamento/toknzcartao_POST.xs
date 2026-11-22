query toknzcartao verb=POST {
  api_group = "Pagamento"
  auth = "user"

  input {
    text creditCardHolderName filters=trim
    text creditCardNumber filters=trim
    text creditCardExpiryMonth filters=trim
    text creditCardExpiryYear filters=trim
    text creditCardCcv filters=trim
  }

  stack {
    // Pega o API Token Assas do SLFood 
    db.get tokens {
      field_name = "Plataforma"
      field_value = "Asaas"
    } as $tokens1
  
    // Pega o Cliente que está logado
    db.get CLIENTE {
      field_name = "user_id"
      field_value = `$auth.id`
    } as $CLIENTE1
  
    // Pega o ID do Cliente Assas
    db.get CARTAOTOKNZD {
      field_name = "cliente_id"
      field_value = $CLIENTE1.id
    } as $CARTAOTOKNZD1
  
    // Pega o ID do Status de TTOKENIZACAO 'Criada'
    db.query STATUS_TTOKENIZACAO {
      where = $db.status_ttokenizacao.status == "Criada"
      return = {type: "list"}
    } as $STATUS_TTOKENIZACAO1
  
    // Cria registro de que TTOKENIZAÇÃO foi Criada
    db.add TTOKENIZACAO {
      enforce_hidden_fields = false
      data = {
        created_at            : "now"
        cliente_id            : $CLIENTE1.id
        det_cartao_encript    : $input.creditCardNumber
        status_ttokenizacao_id: $STATUS_TTOKENIZACAO1[0].id
      }
    } as $TTOKENIZACAO1
  
    // Chama API do Assas
    api.request {
      url = "https://api-sandbox.asaas.com/v3/creditCard/tokenizeCreditCard"
      method = "POST"
      params = {
        creditCard: {
          "holderName": $input.creditCardHolderName,
          "number": $input.creditCardNumber,
          "expiryMonth": $input.creditCardExpiryMonth,
          "expiryYear": $input.creditCardExpiryYear,
          "ccv": $input.creditCardCcv
        }
        customer  : $CARTAOTOKNZD1.codigoclienteassas
      }
    
      headers = []
        |push:"User-Agent: XanoApp/1.0 (contact: otakai@gmail.com)"
        |push:"Accept: application/json"
        |push:$tokens1.token
        |push:"Content-Type: application/json"
      verify_host = false
      verify_peer = false
    } as $api1
  
    conditional {
      if (`$var.api1.response.status` == 200) {
        // Pega o ID do Status de TTOKENIZACAO 'Finalizada'
        db.query STATUS_TTOKENIZACAO {
          where = $db.status_ttokenizacao.status == "Finalizada"
          return = {type: "list"}
        } as $STATUS_TTOKENIZACAO1
      
        // Atualiza com o token do cartão tokenizado
        db.patch CARTAOTOKNZD {
          field_name = "id"
          field_value = `$var.CARTAOTOKNZD1.id`
          data = {token: $api1.response.result.creditCardToken}
        } as $CARTAOTOKNZD2
      }
    
      else {
        // Pega o ID do Status de TTOKENIZACAO 'Cancelada'
        db.query STATUS_TTOKENIZACAO {
          where = $db.status_ttokenizacao.status == "Cancelada"
          return = {type: "list"}
        } as $STATUS_TTOKENIZACAO1
      }
    }
  
    // Registro TTOKENIZAÇÃO
    db.add TTOKENIZACAO {
      enforce_hidden_fields = false
      data = {
        created_at            : "now"
        cliente_id            : $CLIENTE1.id
        det_cartao_encript    : $input.creditCardNumber
        status_ttokenizacao_id: $STATUS_TTOKENIZACAO1[0].id
      }
    } as $TTOKENIZACAO1
  
    // Definir saída da API
    db.query TTOKENIZACAO {
      where = $db.ttokenizacao.id == $TTOKENIZACAO1.id
      return = {type: "list"}
    } as $TTOKENIZACAO2
  }

  response = {TTOKENIZACAO: `$var.TTOKENIZACAO2`}
  guid = "oLqPVD_reRBwTiN9WlmvldEDMvM"
}