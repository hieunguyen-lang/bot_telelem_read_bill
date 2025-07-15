from helpers import helper

text = """
Khach: đoàn văn hải,
Sdt: 0975526753,
Rut: 28.050M,
Phi: 2%,
TienPhi: 581.000,
Tong: 29.050M,
LichCanhBao: 15,
ck_vao: {0},
ck_ra: {28.469M},
Stk: 109002443103 - vietinbank- đoàn van hải,
Note: khách rút 29tr050k - 581k fee  còn lại 28tr469k ck lại giúp em,
"""
parse_message_momo_new = helper.parse_message(text)
print(parse_message_momo_new)