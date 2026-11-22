query Upsercep verb=POST {
  api_group = "Custom"

  input {
    text cep? filters=trim
    text uf? filters=trim
    text cidade? filters=trim
  }

  stack {
    db.query CEP {
      where = $db.CEP.cep == $input.cep
      return = {type: "list"}
    } as $CEP1
  
    conditional {
      if ($var.CEP1[0].cep == $input.cep) {
        db.patch CEP {
          field_name = "id"
          field_value = "$var.CEP1[0].id"
          data = `{'uf':$input.uf, ‘cidade':$input.cidade }`
        } as $CEP2
      }
    
      else {
        db.add CEP {
          enforce_hidden_fields = false
          data = {
            id        : null
            created_at: "now"
            cep       : $input.cep
            uf        : $input.uf
            cidade    : $input.cidade
          }
        } as $CEP2
      }
    }
  }

  response = $CEP2
  guid = "JkrPlwtRTHhysGOGwQQV-P_g444"
}