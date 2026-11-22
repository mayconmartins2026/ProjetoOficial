// Request a one-time magic link to reset password by email
query "reset/request-reset-link" verb=POST {
  api_group = "Authentication"

  input {
    email email filters=trim|lower {
      sensitive = true
    }
  }

  stack {
    db.get user {
      field_name = "email"
      field_value = $input.email
      output = ["id", "email"]
    } as $user

    conditional {
      if ($user != null) {
        var $delivery_failed {
          value = false
        }

        try_catch {
          try {
            function.run "Getting Started Template/generate_magic_link" {
              input = {email: $input.email}
            } as $token_and_email

            var $magic_link {
              value = $env.ggreviews_frontend_url ~ "?magic_token=" ~ $token_and_email.token ~ "&email=" ~ ($token_and_email.email|url_encode)
            }

            api.request {
              url = "https://api.brevo.com/v3/smtp/email"
              method = "POST"
              params = {
                sender: {
                  email: $env.brevo_from_email
                  name : "GGReviews"
                }
                to         : [{email: $token_and_email.email}]
                subject    : "Redefinição de senha do GGReviews"
                htmlContent: "<p>Recebemos uma solicitação para redefinir sua senha do GGReviews.</p><p><a href=\"" ~ $var.magic_link ~ "\">Redefinir senha</a></p><p>Se você não solicitou a redefinição, ignore este e-mail.</p>"
              }
              headers = [
                "api-key: " ~ $env.brevo_api_key
                "Content-Type: application/json"
              ]
            } as $email_response

            conditional {
              if ($email_response.response.status != 201) {
                var.update $delivery_failed {
                  value = true
                }
              }
            }
          }
          catch {
            var.update $delivery_failed {
              value = true
            }
          }
        }

        conditional {
          if ($delivery_failed) {
            debug.log {
              value = "Password reset link generation or email delivery failed."
            }
          }
        }
      }
    }
  }

  response = {message: "If an account exists, a reset link has been sent."}

  tags = ["authentication", "password-reset"]
  guid = "9FLwxi5uOJ24gomL6pqVwy43h78"
}