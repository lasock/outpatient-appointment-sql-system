from passlib.hash import pbkdf2_sha256


def hash_password(password):
    return pbkdf2_sha256.hash(password)

def verify_password(input_pwd, stored_hash):
    return pbkdf2_sha256.verify(input_pwd, stored_hash)



if __name__ == '__main__':
    p = 'sunba'
    hash = hash_password(p)
    print(hash)
    hash = '$pbkdf2-sha256$29000$F4Lw/n.vVer9X4vRupcS4g$gKRAmwTohwzwYBuDqX4b1JxSqx8xJUenTykchgWgUB0'
    print(verify_password('zhangsan', hash))
