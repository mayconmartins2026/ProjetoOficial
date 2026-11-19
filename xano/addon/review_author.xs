// Exposes only the fields needed to identify a review author.
addon review_author {
  input {
    int user_id {
      table = "user"
    }
  }

  stack {
    db.query user {
      where = $db.user.id == $input.user_id
      return = {type: "single"}
      output = ["id", "name", "img_perfil"]
    }
  }
  guid = "heSYNBrLYOBxjQKCRPJgulboS4Q"
}
