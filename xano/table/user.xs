// Stores user information and allows the user to authenticate  against
table user {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    text name filters=trim

    email? email filters=trim|lower
    password? password filters=min:8|minAlpha:1|minDigit:1 {
      visibility = "internal"
    }

    text otp_code? filters=trim
    timestamp? otp_expires_at?

    // Reference to the company the user belongs to.
    int account_id? {
      table = "account"
    }

    // The role of the user within their company (e.g., 'admin', 'member').
    enum role? {
      values = ["admin", "member"]
      visibility = "private"
    }

    object password_reset? {
      schema {
        password token? {
          visibility = "internal"
        }

        timestamp? expiration? {
          visibility = "internal"
        }

        bool used? {
          visibility = "internal"
        }
      }
    }

    int papel_id? {
      table = "PAPEL"
    }

    image? img_perfil?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
  ]

  tags = [
    "xano:quick-start"
    "modulo 01"
    "modulo 02"
    "modulo 03"
    "modulo 04"
    "modulo 05"
  ]

  guid = "g8tpjso2orFaPgdxKGzuuR66M1k"
}
