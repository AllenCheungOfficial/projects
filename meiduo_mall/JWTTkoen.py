import json
import base64

header = {
    'typ': 'JWT',
    'alg': 'HS256'
}
# 将字典转化成json（字符串）
header = json.dumps(header)  # str
# 将json字符串通过base64编码称一个可视化的长字符串（字节对象
header = base64.b64encode(header.encode())

print("header:", header)

payload = {
    "sub": "1234567890",
    "name": "John Doe",
    "admin": True,
}

payload = json.dumps(payload)
payload = base64.b64encode(payload.encode())
print("payload:", payload)

# 组织要加密的数据
msg = header + b"." + payload

import hmac,hashlib
# sha256加密生成签名部分
SECRET_KEY = b'j*h(69kj^)ofyw+re!3!fpsh28a^wnm9iv1xv@9mi%^$)(dgm='

hmac_odj = hmac.new(SECRET_KEY, msg=msg, digestmod=hashlib.sha256)
signature = hmac_odj.hexdigest()
print("signature:",signature)


# 得到的完整JWTTOken值是说明？
# 是后台生成，并交给浏览器的
JWT_Token = header.decode() + '.' + payload.decode() + '.' + signature
print('JWT_Token:', JWT_Token)
print('*'*20+"分割线"+'*'*20)
# 下面的逻辑模拟后台接受浏览器token 值然后进行校验的逻辑
# 下一次浏览器在请求的时候，会携带这个Token值
JWT_Token_from_font = JWT_Token
# JWT_Token_from_font = '123.456.789'


content= JWT_Token_from_font.split('.')
# print(content)

# 通过解析，获得jwt三部分内容
header_from_font = content[0]
payload_from_font = content[1]
signature_from_font = content[2]

# 验证数据的完整性（数据是否被篡改）

# 对浏览器给我们的header_from_font和payload_from_font再一次按照相同的加密方式进行加密
# 对浏览器给我们的签名进行比对
msg = header_from_font + '.' + payload_from_font
new_signature = hmac.new(SECRET_KEY,msg=msg.encode(), digestmod=hashlib.sha256).hexdigest()

if new_signature == signature_from_font:
    print('数据ok')

    # 提取用户数据
    payload = base64.b64decode(payload_from_font.encode()) # json
    print(payload,type(payload))

    payload = json.loads(payload.decode())
    print(payload)
else:
    print("no")
