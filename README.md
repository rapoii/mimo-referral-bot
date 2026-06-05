# 🤖 MiMo Referral Bot

Automated Xiaomi MiMo account creator with referral system and API key generation.

## ✨ Features

- 📧 Auto temp email generation
- 🔄 Automated Xiaomi account registration
- 🤖 reCAPTCHA auto-solve
- 📬 Email verification automation
- 🎁 Referral code auto-apply (+$2 credits)
- 🔑 API Key auto-creation
- 📊 Detailed report generation
- 🔁 Multi-account support

## 📂 Project Structure

```
mimo-referral-bot/
├── mimo_creator.py        # Main script
├── config.example.json    # Config template
├── requirements.txt       # Dependencies
├── pyproject.toml        # Python package config
├── README.md             # Documentation
├── LICENSE               # MIT License
├── .gitignore           # Git ignore rules
└── __init__.py          # Package init
```

## 📋 Prerequisites

- Python 3.9+
- pip

## 🚀 Installation

```bash
# Clone repository
git clone https://github.com/rfpermana/mimo-referral-bot.git
cd mimo-referral-bot

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## 💻 Usage

### Single Account
```bash
python mimo_creator.py
```

### With Custom Referral
```bash
python mimo_creator.py --referral YOUR_CODE
```

### Multiple Accounts
```bash
python mimo_creator.py --referral YOUR_CODE --count 5
```

### With Config File
```bash
# Copy example config
cp config.example.json config.json

# Edit config.json with your settings

# Run with config
python mimo_creator.py --config config.json
```

### Headless Mode (No Browser Window)
```bash
python mimo_creator.py --headless
```

## ⚙️ Configuration

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--referral` | `-r` | CJZ295 | Referral code |
| `--count` | `-c` | 1 | Number of accounts |
| `--password` | `-p` | papoi123 | Account password |
| `--config` | | | Config file path |
| `--headless` | | false | Run without browser |

### Config File (config.json)

```json
{
  "referral_code": "YOUR_CODE",
  "password": "YourPassword123",
  "temp_email_domain": "banri.xyz",
  "headless": false,
  "delay_between_accounts": [10, 30],
  "output_dir": "output"
}
```

## 📁 Output

Reports are saved to:
```
~/mimo-accounts/
├── laporan_YYYYMMDD_HHMMSS.txt  # Report with timestamp
```

### Report Format
```
==================================================
  LAPORAN AUTOMASI AKUN MiMo
  Tanggal: 2026-06-05 21:13:00
==================================================

Total akun: 3
Berhasil: 3
Gagal: 0

--- AKUN #1 ---
Email:    abc123@banri.xyz
Password: papoi123
Balance:  $2.39
API Key:  sk-abc123xyz...
Status:   SUCCESS
Waktu:    2026-06-05T21:13:00.000000

--- AKUN #2 ---
...

==================================================
```

## 📊 Example Output

```
╔══════════════════════════════════════════════╗
║        🤖 MiMo Referral Bot v1.0            ║
║        Automated Account Creator             ║
╚══════════════════════════════════════════════╝

📋 Konfigurasi:
   Referral: CJZ295
   Jumlah:   3 akun
   Password: papoi123

==================================================
🚀 MEMULAI PEMBUATAN AKUN MiMo
==================================================
📧 Email: abc123@banri.xyz
🔗 Referral: CJZ295
==================================================

✅ Step 1 berhasil! (Membuka temp email)
✅ Step 2 berhasil! (Membuka MiMo signup)
✅ Step 3 berhasil! (Klik tombol Sign up)
✅ Step 4 berhasil! (Mengisi form)
✅ Step 5 berhasil! (reCAPTCHA)
✅ Step 6 berhasil! (Ambil kode verifikasi)
✅ Step 7 berhasil! (Masukin kode)
✅ Step 8 berhasil! (Accept terms)
✅ Step 9 berhasil! (Referral applied)
✅ Step 10 berhasil! (Buat API key)

==================================================
✅ AKUN BERHASIL DIBUAT!
==================================================
📧 Email:    abc123@banri.xyz
🔑 Password: papoi123
💰 Balance:  $2.39
🔗 Referral: CJZ295 (applied)
🔑 API Key:  sk-abc123...
==================================================

📊 RINGKASAN
==================================================
Total:    3 akun
✅ Sukses: 3
❌ Gagal:  0

📄 Laporan: ~/mimo-accounts/laporan_20260605_211300.txt
==================================================
```

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Use responsibly and in accordance with Xiaomi's Terms of Service.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⭐ Support

If you find this useful, give it a ⭐ on GitHub!

## 📞 Contact

- GitHub: [@rfpermana](https://github.com/rfpermana)
