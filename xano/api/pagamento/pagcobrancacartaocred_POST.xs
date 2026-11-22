query pagcobrancacartaocred verb=POST {
  api_group = "Pagamento"
  auth = "user"

  input {
    // No Assas  é algo parecido com pay_91krxrq0wav7evqc
    text idcobrancao? filters=trim
  }

  stack {
    // Pega o API Token Assas do SLFood 
    db.get tokens {
      field_name = "plataforma"
      field_value = "Asaas"
    } as $tokens1
  
    // Pega o cliente logado
    db.get CLIENTE {
      field_name = "user_id"
      field_value = $auth.id
    } as $CLIENTE1
  
    // Pega o ID do Cliente Assas
    db.get CARTAOTOKNZD {
      field_name = "cliente_id"
      field_value = $CLIENTE1.id
    } as $CARTAOTOKNZD1
  
    // Pega da transação de pagamento
    db.get "" {
      field_name = "idpayment"
      field_value = $input.idcobrancao
    } as $TRANSACAO1
  
    // Pega status indicando início transação de pagamento
    db.get "" {
      field_name = "status"
      field_value = "Pagamento Iniciado"
    } as $STATUS_TRANSACAO1
  
    // Log início de transação de pagamento
    db.add "" {
      enforce_hidden_fields = false
      data = {
        created_at        : "now"
        clienteassas      : $TRANSACAO1.clienteassas
        idpayment         : $TRANSACAO1.idpayment
        tipo              : $TRANSACAO1.tipo
        valor             : $TRANSACAO1.valor
        datavenc          : $TRANSACAO1.datavenc
        descricao         : $TRANSACAO1.descricao
        statustransacao_id: $STATUS_TRANSACAO1.id
      }
    } as $TRANSACAO2
  
    // Deixa status de erro de transação de pagamento como padrão.
    db.get "" {
      field_name = "status"
      field_value = "Erro no Pagamento da Cobrança"
    } as $STATUS_TRANSACAO1
  
    conditional {
      if (`$var.TRANSACAO1` == null) {
        var $resultado {
          value = [
            {
              "code": "invalid_action",
              "description": "Código de pagamento inexistente!"
            }
          ]
        }
      }
    
      elseif (`$var.TRANSACAO1.clienteassas` != `$var.CARTAOTOKNZD1.codigoclienteassas`) {
        var $resultado {
          value = [
            {
              "code": "invalid_action",
              "description": "Cliente logado não possui esse Código de Pagamento!"
            }
          ]
        }
      }
    
      else {
        api.request {
          url = "https://api-sandbox.asaas.com/v3/payments/pay_91krxrq0wav7evqc/payWithCreditCard"
          method = "POST"
          params = {}
            |set:"id":`$input.idcobrancao`
            |set:"creditCardToken":`$var.CARTAOTOKNZD1.token`
          headers = []
            |push:"User-Agent: XanoApp/1.0 (contact: otakai@gmail.com)"
            |push:"accept: application/json"
            |push:`$var.tokens1.token`
            |push:"content-type: application/json"
          verify_host = false
          verify_peer = false
        } as $api1
      
        conditional {
          if (`$var.api1.response.status` != 200) {
            var $resultado {
              value = `$var.api1.response.result.errors`
            }
          }
        
          else {
            // Pega status indicando sucesso na transação de pagamento
            db.get "" {
              field_name = "status"
              field_value = "Sucesso no Pagamento da Cobrança"
            } as $STATUS_TRANSACAO1
          
            var $resultado {
              value = [
                {
                  "code": "ok_action",
                  "description": "Pagamento realizado com sucesso."
                }
              ]
            }
          }
        }
      }
    }
  
    // Log  transação de pagamento
    db.add "" {
      enforce_hidden_fields = false
      data = {
        created_at        : "now"
        clienteassas      : $TRANSACAO1.clienteassas
        idpayment         : $TRANSACAO1.idpayment
        tipo              : $TRANSACAO1.tipo
        valor             : $TRANSACAO1.valor
        datavenc          : $TRANSACAO1.datavenc
        descricao         : $TRANSACAO1.descricao
        statustransacao_id: $STATUS_TRANSACAO1.id
      }
    } as $TRANSACAO2
  }

  response = {resultado: $resultado}
  guid = "LV1npRPK5egtKM6bu78pTK0tciQ"
}