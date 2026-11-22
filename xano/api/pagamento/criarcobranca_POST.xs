query criarcobranca verb=POST {
  api_group = "Pagamento"
  auth = "user"

  input {
    text tipo filters=trim
    decimal valor filters=min:0
    date datavenc
    text descricao filters=trim
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
  
    db.get CARTAOTOKNZD {
      field_name = "cliente_id"
      field_value = $CLIENTE1.id
    } as $CARTAOTOKNZD1
  
    // Corrigido: Usando headers como uma lista de strings
    api.request {
      url = "https://api-sandbox.asaas.com/v3/payments"
      method = "POST"
      params = {}
        |set:"billingType":$input.tipo
        |set:"customer":$CARTAOTOKNZD1.codigoclienteassas
        |set:"value":$input.valor
        |set:"dueDate":$input.datavenc
        |set:"description":$input.descricao
      headers = []
        |push:"User-Agent: XanoApp/1.0 (contact: otakai@gmail.com)"
        |push:"Accept: application/json"
        |push:$tokens1.token
        |push:"Content-Type: application/json"
      verify_host = false
      verify_peer = false
    } as $api1
  
    conditional {
      // Se deu certo a chamada da API do Assas
      if (`$var.api1.response.status` == 200) {
        db.get "" {
          field_name = "status"
          field_value = "Cobrança Criada"
        } as $STATUSTRANSACAO1
      }
    
      // Não deu certo
      else {
        db.get "" {
          field_name = "status"
          field_value = "Erro na Criação da Cobrança"
        } as $STATUSTRANSACAO1
      }
    }
  
    db.add "" {
      enforce_hidden_fields = false
      data = {
        created_at        : "now"
        clienteassas      : `$var.CARTAOTOKNZD1.codigoclienteassas`
        idpayment         : `$var.api1.response.result.id`
        tipo              : $input.tipo
        valor             : $input.valor
        datavenc          : $input.datavenc
        descricao         : $input.descricao
        statustransacao_id: `$var.STATUSTRANSACAO1.id`
      }
    } as $TRANSACAO1
  }

  response = {TRANSACAO: $TRANSACAO1}
  guid = "Xidv4K5KdY85rx4VKYICOlDba7E"
}