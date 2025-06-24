# bot_telelem_read-_bill

# colname = [
            "Thời gian ghi nhận",        # timestamp
            "Người gửi",                 # full_name
            "Tên khách",                 # caption['khach']
            "Số điện thoại",             # caption['sdt']
            "Số tiền rút",               # caption['rut']
            "Phần trăm phí",            # caption['phi']
            "Số tiền phí",              # caption['tien_phi']
            "Số tiền chuyển khoản",     # caption['chuyen_khoan']
            "Lịch cảnh báo",            # caption['lich_canh_bao']
            "Số tài khoản",             # caption['stk']
            "Ghi chú",                  # caption['note']
            "Ngân hàng",                # result["ten_ngan_hang"]
            "Đơn vị bán hàng",          # result["ten_don_vi_ban"]
            "Địa chỉ đơn vị",           # result["dia_chi_don_vi_ban"]
            "Ngày giao dịch",           # result["ngay_giao_dich"]
            "Giờ giao dịch",            # result["gio_giao_dich"]
            "Tổng số tiền",             # result["tong_so_tien"]
            "Đơn vị tiền tệ",           # result["don_vi_tien_te"]
            "Loại thẻ",                 # result["loai_the"]
            "Mã giao dịch",             # result["ma_giao_dich"]
            "Mã đơn vị chấp nhận",      # result["ma_don_vi_chap_nhan"]
            "Số lô",                    # result["so_lo"]
            "Số tham chiếu",            # result["so_tham_chieu"]
            "Loại giao dịch",           # result["loai_giao_dich"]
            "Caption gốc"               # message.caption
        ]
        
docker exec mysql_bill /usr/bin/mysqldump -u root --password=root bill_data > "C:\Users\Admin\Documents\tool\bot_telelem_read_bill\backup\db_backup.sql"


AIzaSyAStkF_-lQrzja-CTXVvA__9vqVrPwsmTQ

docker network create bill_network
