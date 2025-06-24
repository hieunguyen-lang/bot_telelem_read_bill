
import pytz
from datetime import datetime, timedelta
def send_daily_report():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    tomorrow_day = str(tomorrow.day)
    print(f"Đang gửi báo cáo hàng ngày cho ngày {tomorrow_day}...")

send_daily_report()