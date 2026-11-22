query cadastraCliente verb=POST {
  api_group = "Custom"

  input {
    text nome? filters=trim
    email email? filters=trim|lower
    password senha? {
      sensitive = true
      visibility = "internal"
    }
  
    text celular? filters=trim
    text cpf? filters=trim
    text status? filters=trim
  }

  stack {
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:ZnpRG7wg/auth/signup"
      method = "POST"
      params = {
        name    : $input.nome
        email   : $input.email
        password: $input.senha
      }
    
      headers = ["Content-Type: application/json"]
    } as $api1
  
    api.request {
      url = "https://x8ki-letl-twmt.n7.xano.io/api:ZnpRG7wg/auth/me"
      method = "GET"
      params = `$var.api1.response.result.authToken`
      headers = [
        "Authorization: Bearer " ~ $var.api1.response.result.authToken
        "Content-Type: application/json"
      ]
    
    } as $api2
  
    db.query STATUS_CLIENTE {
      where = $input.status == $db.STATUS_CLIENTE.status
      return = {type: "list"}
    } as $STATUS_CLIENTE1
  
    db.add CLIENTE {
      enforce_hidden_fields = false
      data = {
        created_at       : "now"
        nome             : $input.nome
        celular          : $input.celular
        cpf              : $input.cpf
        user_id          : `$var.api2.response.result.id`
        status_cliente_id: $var.STATUS_CLIENTE1[0].id
      }
    } as $CLIENTE1
  }

  response = {
    user     : $api2.response.result
    cliente  : $CLIENTE1
    authToken: $api1.response.result.authToken
  }

  guid = "GHkSjmsHlToJvvvGZ79XRsy-shE"
}