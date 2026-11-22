# ก้าวสู่ 7,000

Dashboard ติดตามจำนวนก้าว เป้าหมาย 7,000 ก้าวต่อวัน

- หน้าเว็บ: https://surasitman.github.io/mtecstep/
- เปิดหน้าแล้วจะโหลดไฟล์ CSV ล่าสุดใน `data/` ให้อัตโนมัติ โดยอ่านรายชื่อไฟล์จาก `data/manifest.json`
- `summary.html` คือรายงานสรุปและระบบรางวัลจากข้อมูล 1–18 พ.ย.

## เพิ่มข้อมูลชุดใหม่

repo นี้เป็น public ทุกไฟล์ที่ push ขึ้นมาจะเปิดดูได้ทั่วไป และยังอยู่ในประวัติ git แม้จะลบไฟล์ภายหลัง
ดังนั้นต้องตัดคอลัมน์ที่ไม่ใช้ออกก่อน commit ทุกครั้ง

```powershell
python tools/prepare_csv.py "C:\path\to\export.csv"
git add data
git commit -m "Add data"
git push
```

สคริปต์จะทำสิ่งต่อไปนี้:

- เก็บเฉพาะแถวที่ `activityType = steps`
- ตัดบัญชีแอดมินออก
- เก็บเฉพาะคอลัมน์ date, time, firstname, lastname, groupId, groupName, activityType, source, steps
  (ตัดเพศ น้ำหนัก BMI รหัสพนักงาน และคอลัมน์อื่นทิ้ง)
- เขียนไฟล์ผลลัพธ์ลง `data/` แล้วสร้าง `data/manifest.json` ใหม่

หลัง push แล้ว GitHub Action `Prepare data` จะรันสคริปต์ซ้ำอีกรอบ เพื่ออัปเดตเวลาใน manifest
และตัดคอลัมน์ที่อาจหลุดมา แต่ Action รันหลังจากไฟล์เข้า git ไปแล้ว จึงใช้แทนการรันสคริปต์ก่อน commit ไม่ได้
