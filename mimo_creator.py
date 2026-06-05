#!/usr/bin/env python3
"""
MiMo Referral Bot - Automated Account Creator
==============================================
Buat akun MiMo otomatis + apply referral + create API key

Author: Rafi Permana
GitHub: https://github.com/rapoii/mimo-referral-bot
"""

import asyncio
import random
import string
import re
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    print("❌ Error: Playwright belum diinstall!")
    print("   Jalankan: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from playwright_stealth import Stealth
    stealth_instance = Stealth()
except ImportError:
    stealth_instance = None
    print("⚠️  playwright-stealth tidak diinstall, reCAPTCHA mungkin tidak auto-solve")


# ============================================
# KONFIGURASI
# ============================================
DEFAULT_CONFIG = {
    "referral_code": "CJZ295",
    "password": "papoi123",
    "temp_email_domain": "banri.xyz",
    "headless": False,
    "delay_between_accounts": [10, 30],
    "output_dir": str(Path.home() / "mimo-accounts")
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            config.update(user_config)
    return config


def random_username(length: int = 6) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def extract_verification_code(text: str) -> Optional[str]:
    patterns = [
        r'verification code is (\d{6})',
        r'verification code:\s*(\d{6})',
        r'your verification code is:\s*(\d{6})',
        r'\b(\d{6})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


# ============================================
# MiMo Creator Class
# ============================================
class MiMoCreator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.referral = config['referral_code']
        self.password = config['password']
        self.domain = config['temp_email_domain']
        self.username = random_username()
        self.email = f"{self.username}@{self.domain}"
        self.results: Dict[str, Any] = {}
        self.page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None

    async def create_account(self, playwright) -> Dict[str, Any]:
        self._print_header()
        
        browser = await playwright.chromium.launch(
            headless=self.config['headless'],
            slow_mo=300
        )
        self.context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            locale='en-US',
        )
        self.page = await self.context.new_page()
        
        # Apply stealth untuk bypass reCAPTCHA detection
        if stealth_instance:
            await stealth_instance.apply_stealth_async(self.page)
            print("   🛡️  Stealth mode aktif")
        
        try:
            # STEP 1: Buka temp email & ambil email address
            print("\n📧 [1/8] Membuka temp email...")
            await self.page.goto(f"https://generator.email/{self.domain}/{self.username}")
            await self.page.wait_for_timeout(2000)
            print(f"   ✅ Email: {self.email}")
            
            # STEP 2: Buka halaman Xiaomi signup
            print("\n🌐 [2/8] Membuka Xiaomi signup...")
            await self.page.goto("https://account.xiaomi.com/pass/register?_locale=en_US")
            await self.page.wait_for_timeout(3000)
            
            # STEP 3: Isi form registrasi
            print("\n✍️  [3/8] Mengisi form registrasi...")
            
            # Email
            email_input = self.page.locator('input[name="email"]')
            await email_input.fill(self.email)
            print(f"   📧 Email: {self.email}")
            
            # Password
            pwd_input = self.page.locator('input[name="password"]')
            await pwd_input.fill(self.password)
            print(f"   🔑 Password diisi")
            
            # Confirm password
            repwd_input = self.page.locator('input[name="repassword"]')
            await repwd_input.fill(self.password)
            print(f"   🔑 Confirm password diisi")
            
            # Agreement checkbox
            checkbox = self.page.locator('input[type="checkbox"]').first
            await checkbox.check()
            print(f"   ☑️  Agreement dicentang")
            
            # STEP 4: Klik Next + handle reCAPTCHA
            print("\n🔒 [4/8] Klik Next & handle reCAPTCHA...")
            next_btn = self.page.locator('button:has-text("Next")')
            await next_btn.click()
            await self.page.wait_for_timeout(3000)
            
            # Cek reCAPTCHA (muncul SETELAH klik Next)
            print("   🔍 Mencari reCAPTCHA...")
            recaptcha = self.page.locator('iframe[src*="recaptcha"], iframe[title*="reCAPTCHA"], .g-recaptcha')
            count = await recaptcha.count()
            print(f"   📊 reCAPTCHA elements: {count}")
            
            if count > 0:
                # reCAPTCHA ditemukan - coba auto-solve
                frame = recaptcha.first
                content_frame = frame.content_frame
                if content_frame:
                    checkbox_el = content_frame.locator('#recaptcha-anchor')
                    if await checkbox_el.count() > 0:
                        print("   ☑️  Klik reCAPTCHA checkbox...")
                        await checkbox_el.click()
                        await self.page.wait_for_timeout(5000)
                        
                        # Cek apakah solved
                        for i in range(30):
                            try:
                                checked = await checkbox_el.get_attribute('aria-checked')
                                if checked == 'true':
                                    print("   ✅ reCAPTCHA auto-solved!")
                                    break
                                
                                # Cek challenge
                                challenge = content_frame.locator('.rc-imageselect-challenge')
                                if await challenge.count() > 0:
                                    print("")
                                    print("   " + "="*50)
                                    print("   ⚠️  IMAGE CHALLENGE TERDETEKSI!")
                                    print("   ⚠️  Silakan solve MANUAL di browser!")
                                    print("   ⏳ Menunggu 120 detik...")
                                    print("   " + "="*50)
                                    print("")
                                    await self.page.wait_for_timeout(120000)
                                    break
                                
                                await self.page.wait_for_timeout(1000)
                            except:
                                await self.page.wait_for_timeout(1000)
            else:
                # Tidak ada reCAPTCHA iframe - mungkin ada challenge popup
                # Atau reCAPTCHA belum load - tunggu lebih lama
                await self.page.wait_for_timeout(5000)
                
                # Cek apakah sudah redirect ke verify
                current_url = self.page.url
                if 'verify' not in current_url and 'code' not in current_url:
                    print("")
                    print("   " + "="*50)
                    print("   ⚠️  reCAPTCHA MUNGKIN MUNCUL SEBAGAI POPUP")
                    print("   ⚠️  Silakan solve MANUAL di browser!")
                    print("   ⏳ Menunggu 120 detik untuk solve...")
                    print("   " + "="*50)
                    print("")
                    # Tunggu user solve manual
                    await self.page.wait_for_timeout(120000)
            
            # Cek apakah sudah redirect ke verify
            await self.page.wait_for_timeout(3000)
            current_url = self.page.url
            print(f"   📍 URL setelah reCAPTCHA: {current_url[:80]}...")
            
            if 'verify' not in current_url and 'code' not in current_url:
                # Mungkin perlu klik Next lagi setelah reCAPTCHA
                next_btn = self.page.locator('button:has-text("Next")')
                if await next_btn.count() > 0:
                    await next_btn.click()
                    await self.page.wait_for_timeout(5000)
                    current_url = self.page.url
                    print(f"   📍 URL setelah klik ulang Next: {current_url[:80]}...")
            
            # STEP 5: Ambil kode verifikasi dari email
            print("\n📬 [5/8] Mengambil kode verifikasi...")
            email_page = await self.context.new_page()
            await email_page.goto(f"https://generator.email/{self.domain}/{self.username}")
            await email_page.wait_for_timeout(5000)
            
            # Refresh untuk memastikan email masuk
            refresh_btn = email_page.locator('text=Refresh, button:has-text("Refresh")')
            if await refresh_btn.count() > 0:
                await refresh_btn.first.click()
                await email_page.wait_for_timeout(3000)
            
            content = await email_page.content()
            code = extract_verification_code(content)
            
            if not code:
                await email_page.reload()
                await email_page.wait_for_timeout(5000)
                content = await email_page.content()
                code = extract_verification_code(content)
            
            await email_page.close()
            
            if not code:
                print("   ❌ Gagal mendapatkan kode verifikasi!")
                raise Exception("Kode verifikasi tidak ditemukan")
            
            print(f"   ✅ Kode: {code}")
            self.results['verification_code'] = code
            
            # STEP 6: Masukin kode verifikasi
            print("\n🔢 [6/8] Memasukkan kode verifikasi...")
            code_input = self.page.locator('input[placeholder*="code"], input[name*="code"]')
            if await code_input.count() > 0:
                await code_input.first.fill(code)
            else:
                # OTP style
                for i, digit in enumerate(code):
                    otp = self.page.locator(f'input[aria-label*="{i+1}"]')
                    if await otp.count() > 0:
                        await otp.first.fill(digit)
                        await self.page.wait_for_timeout(100)
            
            submit_btn = self.page.locator('button:has-text("Submit")')
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await self.page.wait_for_timeout(5000)
            
            print(f"   ✅ Kode {code} dimasukkan")
            
            # STEP 7: Accept Terms & masukin referral
            print("\n📋 [7/8] Accept Terms & referral...")
            await self.page.wait_for_timeout(3000)
            
            # Accept terms popup
            terms_checkbox = self.page.locator('input[type="checkbox"]').first
            if await terms_checkbox.count() > 0:
                await terms_checkbox.check()
                await self.page.wait_for_timeout(500)
            
            confirm_btn = self.page.locator('button:has-text("Confirm")')
            if await confirm_btn.count() > 0:
                await confirm_btn.click()
                await self.page.wait_for_timeout(2000)
            
            # Masukin referral code
            await self.page.goto("https://platform.xiaomimimo.com/console/balance")
            await self.page.wait_for_timeout(5000)
            
            invite_btn = self.page.locator('button:has-text("Enter invite code"), text=Enter invite code, button:has-text("Bind Code"), text=Bind Code')
            if await invite_btn.count() > 0:
                await invite_btn.first.click()
                await self.page.wait_for_timeout(3000)
                
                # Isi kode
                otp_inputs = self.page.locator('input[type="text"], input[role="textbox"]')
                count = await otp_inputs.count()
                if count >= 6:
                    for i, char in enumerate(self.referral[:6]):
                        await otp_inputs.nth(i).fill(char)
                        await self.page.wait_for_timeout(100)
                    
                    # Redeem
                    redeem_btn = self.page.locator('button:has-text("Redeem"), text=Redeem')
                    if await redeem_btn.count() > 0:
                        await redeem_btn.first.click()
                        await self.page.wait_for_timeout(3000)
                    
                    print(f"   ✅ Referral {self.referral} applied!")
                else:
                    print(f"   ⚠️  Input OTP kurang ({count} dari 6)")
            else:
                print("   ⚠️  Tombol invite code tidak ditemukan")
            
            # Ambil balance
            balance_text = "unknown"
            try:
                balance_el = self.page.locator('text=/\\$ [\\d.]+/')
                if await balance_el.count() > 0:
                    balance_text = (await balance_el.first.text_content()).replace('$', '').strip()
            except:
                pass
            self.results['balance'] = balance_text
            
            # STEP 8: Buat API Key
            print("\n🔑 [8/8] Membuat API Key...")
            await self.page.goto("https://platform.xiaomimimo.com/console/api-keys")
            await self.page.wait_for_timeout(5000)
            
            create_btn = self.page.locator('button:has-text("Create API Key"), text=Create API Key')
            if await create_btn.count() > 0:
                await create_btn.first.click()
                await self.page.wait_for_timeout(3000)
                
                # Isi nama
                name_input = self.page.locator('input[placeholder*="enter"], input[placeholder*="name"]')
                if await name_input.count() > 0:
                    api_name = f"mimo-{self.username}"
                    await name_input.first.fill(api_name)
                
                # Confirm
                confirm_btn = self.page.locator('button:has-text("Confirm")')
                if await confirm_btn.count() > 0:
                    await confirm_btn.click()
                    await self.page.wait_for_timeout(3000)
                
                # Ambil API key
                api_input = self.page.locator('input[disabled], input[readonly]')
                if await api_input.count() > 0:
                    api_key = await api_input.first.input_value()
                    if api_key and len(api_key) > 10:
                        self.results['api_key'] = api_key
                        print(f"   ✅ API Key: {api_key[:30]}...")
                    else:
                        print("   ⚠️  API key kosong")
                else:
                    print("   ⚠️  API key input tidak ditemukan")
            else:
                print("   ⚠️  Tombol Create API Key tidak ditemukan")
            
            # Simpan hasil
            self.results.update({
                'email': self.email,
                'password': self.password,
                'referral': self.referral,
                'created_at': datetime.now().isoformat(),
                'status': 'SUCCESS'
            })
            
            self._print_success()
            return self.results
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self.results = {
                'email': self.email,
                'password': self.password,
                'status': 'FAILED',
                'error': str(e),
                'created_at': datetime.now().isoformat()
            }
            return self.results
            
        finally:
            await browser.close()

    def _print_header(self) -> None:
        print(f"\n{'='*50}")
        print(f"🚀 MEMULAI PEMBUATAN AKUN MiMo")
        print(f"{'='*50}")
        print(f"📧 Email: {self.email}")
        print(f"🔗 Referral: {self.referral}")
        print(f"{'='*50}")

    def _print_success(self) -> None:
        print(f"\n{'='*50}")
        print(f"✅ AKUN BERHASIL DIBUAT!")
        print(f"{'='*50}")
        print(f"📧 Email:    {self.email}")
        print(f"🔑 Password: {self.password}")
        print(f"💰 Balance:  ${self.results.get('balance', 'unknown')}")
        print(f"🔗 Referral: {self.referral} (applied)")
        if 'api_key' in self.results:
            print(f"🔑 API Key:  {self.results['api_key'][:40]}...")
        print(f"{'='*50}\n")


# ============================================
# Report Generator
# ============================================
class ReportGenerator:
    @staticmethod
    def save_report(results_list: List[Dict], output_dir: str) -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"laporan_{timestamp}.txt"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("  LAPORAN AUTOMASI AKUN MiMo\n")
            f.write(f"  Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            success = [r for r in results_list if r.get('status') == 'SUCCESS']
            failed = [r for r in results_list if r.get('status') == 'FAILED']
            
            f.write(f"Total akun: {len(results_list)}\n")
            f.write(f"Berhasil: {len(success)}\n")
            f.write(f"Gagal: {len(failed)}\n\n")
            
            for i, r in enumerate(results_list, 1):
                f.write(f"--- AKUN #{i} ---\n")
                f.write(f"Email:    {r.get('email', '-')}\n")
                f.write(f"Password: {r.get('password', '-')}\n")
                f.write(f"Balance:  ${r.get('balance', '-')}\n")
                f.write(f"API Key:  {r.get('api_key', '-')}\n")
                f.write(f"Status:   {r.get('status', '-')}\n")
                if 'error' in r:
                    f.write(f"Error:    {r['error']}\n")
                f.write(f"Waktu:    {r.get('created_at', '-')}\n\n")
            
            f.write("=" * 50 + "\n")
        
        return filepath


# ============================================
# Main
# ============================================
async def main():
    parser = argparse.ArgumentParser(
        description='MiMo Referral Bot - Automated Account Creator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--referral', '-r', default=DEFAULT_CONFIG['referral_code'])
    parser.add_argument('--count', '-c', type=int, default=1)
    parser.add_argument('--password', '-p', default=DEFAULT_CONFIG['password'])
    parser.add_argument('--config', help='Path ke file config.json')
    parser.add_argument('--headless', action='store_true')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    config['referral_code'] = args.referral
    config['password'] = args.password
    config['headless'] = args.headless
    
    print("""
╔══════════════════════════════════════════════╗
║        🤖 MiMo Referral Bot v1.0            ║
║        Automated Account Creator             ║
╚══════════════════════════════════════════════╝
    """)
    print(f"📋 Referral: {config['referral_code']}")
    print(f"📋 Jumlah:   {args.count} akun")
    print(f"📋 Headless: {config['headless']}")
    print()
    
    results = []
    
    async with async_playwright() as playwright:
        for i in range(args.count):
            print(f"\n🔄 Membuat akun {i+1}/{args.count}...")
            creator = MiMoCreator(config)
            result = await creator.create_account(playwright)
            if result:
                results.append(result)
            
            if i < args.count - 1:
                delay = random.randint(*config['delay_between_accounts'])
                print(f"⏳ Menunggu {delay} detik...")
                await asyncio.sleep(delay)
    
    report_path = ReportGenerator.save_report(results, config['output_dir'])
    
    success = [r for r in results if r.get('status') == 'SUCCESS']
    print(f"\n{'='*50}")
    print(f"📊 RINGKASAN: {len(success)}/{len(results)} berhasil")
    print(f"📄 Laporan: {report_path}")
    print(f"{'='*50}\n")
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Dibatalkan oleh user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
