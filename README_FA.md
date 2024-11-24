
# ربات گزارش روزانه

این ربات تلگرام برای کمک به تیم‌ها در تکمیل و مدیریت گزارش‌های روزانه طراحی شده است. ربات از SQLite برای ذخیره‌سازی استفاده می‌کند و قابلیت اجرا به‌صورت کانتینر Docker را داراست.

**[بازگشت به نسخه انگلیسی](README.md)**

---

## ویژگی‌ها

1. **گزارش‌های روزانه**:
   - کاربران می‌توانند گزارش‌های روزانه خود را شامل موارد زیر ارسال کنند:
     - کارهایی که امروز انجام داده‌اند.
     - سوالات یا موانعی که با آنها روبرو شده‌اند.
     - کارهایی که برای فردا برنامه‌ریزی کرده‌اند.

2. **یادآوری خودکار**:
   - ارسال یادآوری برای تکمیل گزارش به کاربران.
   - اطلاع‌رسانی به گروه درباره گزارش‌های ناقص.

3. **خلاصه گزارش‌ها**:
   - ارسال گزارش‌های تجمیعی روزانه به گروه.

4. **استفاده از Docker**:
   - قابلیت اجرا به‌صورت کانتینر Docker برای ساده‌سازی راه‌اندازی و مدیریت.

---

## تنظیمات Docker

### Dockerfile

فایل `Dockerfile` برای ساخت یک کانتینر سبک طراحی شده است:

```dockerfile
# استفاده از تصویر رسمی Python از Docker Hub
FROM python:3.9-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# تنظیم متغیر محیطی پراکسی (در صورت نیاز)
ENV http_proxy=${HTTP_PROXY}

# کپی فایل‌های موردنیاز به کانتینر
COPY requirements.txt .

# نصب پکیج‌های مورد نیاز
RUN pip install --no-cache-dir -r requirements.txt

# کپی بقیه فایل‌های برنامه
COPY ./ScrumAssistance-full.py .

# دستور اجرا
CMD ["python", "ScrumAssistance-full.py"]
```

---

### Docker Compose

فایل `docker-compose.yml` برای تنظیم سرویس‌ها و مدیریت داده‌ها:

```yaml
version: "3.1"

services:
  dailyreporter:
    container_name: dailyreporter
    build: .
    logging:
      options:
        max-size: "500m"
        max-file: "5"
    volumes:
      - daily-reporter-data:/app/data
    env_file: .env
    networks:
      - telegram-network

networks:
  telegram-network:
    driver: bridge

volumes:
  daily-reporter-data:
    driver: local
    driver_opts:
      o: bind
      type: none
      device: "./dailyreporter"
```

---

## راه‌اندازی

### اجرا به‌صورت محلی

1. کد ربات را دانلود کنید یا فایل‌های اسکریپت را کپی کنید.
2. وابستگی‌ها را نصب کنید:
   ```bash
   pip install -r requirements.txt
   ```
3. اجرای ربات:
   ```bash
   python ScrumAssistance-full.py
   ```

### اجرا با Docker

1. ساخت تصویر Docker:
   ```bash
   docker-compose build
   ```
2. راه‌اندازی ربات:
   ```bash
   docker-compose up
   ```
3. متوقف کردن ربات:
   ```bash
   docker-compose down
   ```

---

برای بازگشت به **[نسخه انگلیسی](README.md)** اینجا کلیک کنید.
