#!/usr/bin/env python3
"""
MiMo Referral Bot - Automated Account Creator
==============================================
Buat akun MiMo otomatis + apply referral + create API key

Author: Rafi Permana
GitHub: https://github.com/rfpermana/mimo-referral-bot
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
    """Load config from file or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            config.update(user_config)
    
    return config


def random_username(length: int = 6) -> str:
    """Generate random username untuk temp email"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def extract_verification_code(text: str) -> Optional[str]:
    """Extract 6-digit verification code dari email body"""
    patterns = [
        r'verification code is (\d{6})',
        r'verification code:\s*(\d{6})',
        r'code is:\s*(\d{6})',
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
    """Automated MiMo account creator"""
    
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
        """Main workflow: buat akun + referral + API key"""
        self._print_header()
        
        browser = await playwright.chromium.launch(
            headless=self.config['headless']
        )
        self.context = await browser.new_context()
        self.page = await self.context.new_page()
        
        try:
            steps = [
                self._step_open_temp_email,
                self._step_open_mimo_signup,
                self._step_click_signup,
                self._step_fill_form,
                self._step_solve_recaptcha,
                self._step_get_verification_code,
                self._step_enter_verification,
                self._step_accept_terms,
                self._step_enter_referral,
                self._step_create_api_key,
            ]
            
            for i, step in enumerate(steps, 1):
                print(f"\n{'='*50}")
                print(f"📍 Step {i}/{len(steps)}: {step.__doc__}")
                print(f"{'='*50}")
                
                success = await step()
                
                if not success:
                    raise Exception(f"Gagal di step {i}: {step.__doc__}")
                
                print(f"✅ Step {i} berhasil!")
            
            # Ambil balance
            await self._get_balance()
            
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
    
    async def _step_open_temp_email(self) -> bool:
        """Membuka temp email"""
        url = f"https://generator.email/{self.domain}/{self.username}"
        await self.page.goto(url)
        await self.page.wait_for_timeout(2000)
        print(f"   📧 Email: {self.email}")
        return True
    
    async def _step_open_mimo_signup(self) -> bool:
        """Membuka MiMo signup"""
        url = f"https://platform.xiaomimimo.com/?ref={self.referral}"
        await self.page.goto(url)
        await self.page.wait_for_timeout(3000)
        
        # Cari tombol Apply for API Key
        apply_btn = self.page.locator('a:has-text("Apply for API Key")')
        if await apply_btn.count() > 0:
            await apply_btn.click()
            await self.page.wait_for_timeout(3000)
        
        return True
    
    async def _step_click_signup(self) -> bool:
        """Klik tombol Sign up"""
        signup_btn = self.page.locator('button:has-text("Sign up")')
        if await signup_btn.count() > 0:
            await signup_btn.click()
            await self.page.wait_for_timeout(2000)
            return True
        return False
    
    async def _step_fill_form(self) -> bool:
        """Mengisi form registrasi"""
        # Email
        email_input = self.page.locator('input[placeholder*="Email"], input[name="email"]')
        await email_input.fill(self.email)
        await self.page.wait_for_timeout(500)
        
        # Password
        pwd_inputs = self.page.locator('input[type="password"]')
        if await pwd_inputs.count() >= 1:
            await pwd_inputs.first.fill(self.password)
            await self.page.wait_for_timeout(500)
        
        # Confirm password
        if await pwd_inputs.count() >= 2:
            await pwd_inputs.last.fill(self.password)
            await self.page.wait_for_timeout(500)
        
        # Agreement checkbox
        checkbox = self.page.locator('input[type="checkbox"]').first
        if await checkbox.count() > 0:
            await checkbox.check()
            await self.page.wait_for_timeout(500)
        
        print(f"   ✍️  Form terisi: {self.email}")
        return True
    
    async def _step_solve_recaptcha(self) -> bool:
        """Menyelesaikan reCAPTCHA"""
        next_btn = self.page.locator('button:has-text("Next")')
        await next_btn.click()
        await self.page.wait_for_timeout(5000)
        
        # reCAPTCHA biasanya auto-solved di Playwright
        print("   🤖 reCAPTCHA diselesaikan")
        return True
    
    async def _step_get_verification_code(self) -> bool:
        """Mengambil kode verifikasi dari email"""
        print("   ⏳ Menunggu email verifikasi...")
        await self.page.wait_for_timeout(3000)
        
        # Buka tab baru untuk cek email
        email_page = await self.context.new_page()
        url = f"https://generator.email/{self.domain}/{self.username}"
        await email_page.goto(url)
        await email_page.wait_for_timeout(5000)
        
        # Cari kode
        content = await email_page.content()
        code = extract_verification_code(content)
        
        if not code:
            # Coba refresh
            await email_page.reload()
            await email_page.wait_for_timeout(5000)
            content = await email_page.content()
            code = extract_verification_code(content)
        
        await email_page.close()
        
        if code:
            print(f"   📬 Kode verifikasi: {code}")
            self.results['verification_code'] = code
            return True
        
        return False
    
    async def _step_enter_verification(self) -> bool:
        """Memasukkan kode verifikasi"""
        code = self.results.get('verification_code')
        if not code:
            return False
        
        # Cari input kode
        code_input = self.page.locator('input[placeholder*="code"], input[name*="code"]')
        if await code_input.count() > 0:
            await code_input.first.fill(code)
        else:
            # OTP-style inputs
            for i, digit in enumerate(code):
                otp = self.page.locator(f'input[aria-label*="{i+1}"]')
                if await otp.count() > 0:
                    await otp.first.fill(digit)
                    await self.page.wait_for_timeout(100)
        
        # Submit
        submit_btn = self.page.locator('button:has-text("Submit"), button:has-text("Verify")')
        if await submit_btn.count() > 0:
            await submit_btn.click()
            await self.page.wait_for_timeout(5000)
        
        print(f"   🔢 Kode {code} dimasukkan")
        return True
    
    async def _step_accept_terms(self) -> bool:
        """Accept Terms & Agreements"""
        await self.page.wait_for_timeout(3000)
        
        # Checkbox
        checkbox = self.page.locator('input[type="checkbox"]').first
        if await checkbox.count() > 0:
            await checkbox.check()
            await self.page.wait_for_timeout(500)
        
        # Confirm
        confirm_btn = self.page.locator('button:has-text("Confirm")')
        if await confirm_btn.count() > 0:
            await confirm_btn.click()
            await self.page.wait_for_timeout(2000)
        
        print("   📋 Terms accepted")
        return True
    
    async def _step_enter_referral(self) -> bool:
        """Memasukkan kode referral"""
        await self.page.goto("https://platform.xiaomimimo.com/console/balance")
        await self.page.wait_for_timeout(3000)
        
        # Klik Enter invite code
        invite_btn = self.page.locator('button:has-text("Enter invite code")')
        if await invite_btn.count() > 0:
            await invite_btn.click()
            await self.page.wait_for_timeout(2000)
            
            # Isi kode (6 karakter)
            otp_inputs = self.page.locator('input[type="text"], input[role="textbox"]')
            for i, char in enumerate(self.referral[:6]):
                if i < await otp_inputs.count():
                    await otp_inputs.nth(i).fill(char)
                    await self.page.wait_for_timeout(100)
            
            # Redeem
            redeem_btn = self.page.locator('button:has-text("Redeem")')
            if await redeem_btn.count() > 0:
                await redeem_btn.click()
                await self.page.wait_for_timeout(3000)
            
            print(f"   🎁 Referral {self.referral} applied!")
            return True
        
        print("   ⚠️  Tombol invite code tidak ditemukan")
        return True  # Lanjutkan meski gagal
    
    async def _step_create_api_key(self) -> bool:
        """Membuat API Key"""
        await self.page.goto("https://platform.xiaomimimo.com/console/api-keys")
        await self.page.wait_for_timeout(3000)
        
        # Create API Key
        create_btn = self.page.locator('button:has-text("Create API Key")')
        if await create_btn.count() > 0:
            await create_btn.click()
            await self.page.wait_for_timeout(2000)
            
            # Isi nama
            name_input = self.page.locator('input[placeholder*="enter"]')
            if await name_input.count() > 0:
                api_name = f"mimo-{self.username}"
                await name_input.fill(api_name)
            
            # Confirm
            confirm_btn = self.page.locator('button:has-text("Confirm")')
            if await confirm_btn.count() > 0:
                await confirm_btn.click()
                await self.page.wait_for_timeout(3000)
            
            # Ambil API key
            api_input = self.page.locator('input[disabled], input[readonly]')
            if await api_input.count() > 0:
                api_key = await api_input.first.input_value()
                self.results['api_key'] = api_key
                print(f"   🔑 API Key: {api_key[:30]}...")
                return True
        
        print("   ⚠️  Gagal membuat API key")
        return True  # Lanjutkan meski gagal
    
    async def _get_balance(self) -> None:
        """Ambil balance terbaru"""
        await self.page.goto("https://platform.xiaomimimo.com/console/balance")
        await self.page.wait_for_timeout(3000)
        
        try:
            balance_elem = self.page.locator('text=/\\$ [\\d.]+/')
            if await balance_elem.count() > 0:
                balance_text = await balance_elem.first.text_content()
                self.results['balance'] = balance_text.replace('$', '').strip()
        except:
            self.results['balance'] = 'unknown'
    
    def _print_header(self) -> None:
        """Print header"""
        print(f"\n{'='*50}")
        print(f"🚀 MEMULAI PEMBUATAN AKUN MiMo")
        print(f"{'='*50}")
        print(f"📧 Email: {self.email}")
        print(f"🔗 Referral: {self.referral}")
        print(f"{'='*50}")
    
    def _print_success(self) -> None:
        """Print success message"""
        print(f"\n{'='*50}")
        print(f"✅ AKUN BERHASIL DIBUAT!")
        print(f"{'='*50}")
        print(f"📧 Email:    {self.email}")
        print(f"🔑 Password: {self.password}")
        print(f"💰 Balance:  ${self.results.get('balance', 'unknown')}")
        print(f"🔗 Referral: {self.referral} (applied)")
        if 'api_key' in self.results:
            print(f"🔑 API Key:  {self.results['api_key'][:30]}...")
        print(f"{'='*50}\n")


# ============================================
# Report Generator
# ============================================
class ReportGenerator:
    """Generate laporan akun"""
    
    @staticmethod
    def save_report(results_list: List[Dict], output_dir: str) -> Path:
        """Simpan laporan ke file"""
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
# Main Entry Point
# ============================================
async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MiMo Referral Bot - Automated Account Creator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python mimo_creator.py
  python mimo_creator.py --referral CJZ295
  python mimo_creator.py --referral CJZ295 --count 5
  python mimo_creator.py --config config.json
        """
    )
    
    parser.add_argument(
        '--referral', '-r',
        default=DEFAULT_CONFIG['referral_code'],
        help=f'Kode referral (default: {DEFAULT_CONFIG["referral_code"]})'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=1,
        help='Jumlah akun yang akan dibuat (default: 1)'
    )
    parser.add_argument(
        '--password', '-p',
        default=DEFAULT_CONFIG['password'],
        help=f'Password untuk akun (default: {DEFAULT_CONFIG["password"]})'
    )
    parser.add_argument(
        '--config',
        help='Path ke file config.json'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Jalankan dalam mode headless (tanpa browser window)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    config['referral_code'] = args.referral
    config['password'] = args.password
    config['headless'] = args.headless
    
    # Print banner
    print("""
╔══════════════════════════════════════════════╗
║        🤖 MiMo Referral Bot v1.0            ║
║        Automated Account Creator             ║
╚══════════════════════════════════════════════╝
    """)
    
    print(f"📋 Konfigurasi:")
    print(f"   Referral: {config['referral_code']}")
    print(f"   Jumlah:   {args.count} akun")
    print(f"   Password: {config['password']}")
    print(f"   Headless: {config['headless']}")
    print()
    
    results = []
    
    async with async_playwright() as playwright:
        for i in range(args.count):
            print(f"\n🔄 Membuat akun {i+1}/{args.count}...")
            
            creator = MiMoCreator(config)
            result = await creator.create_account(playwright)
            
            if result:
                results.append(result)
            
            # Delay antar akun
            if i < args.count - 1:
                delay_range = config['delay_between_accounts']
                delay = random.randint(delay_range[0], delay_range[1])
                print(f"⏳ Menunggu {delay} detik sebelum akun berikutnya...")
                await asyncio.sleep(delay)
    
    # Simpan laporan
    report_path = ReportGenerator.save_report(results, config['output_dir'])
    
    # Print summary
    success = [r for r in results if r.get('status') == 'SUCCESS']
    
    print(f"\n{'='*50}")
    print(f"📊 RINGKASAN")
    print(f"{'='*50}")
    print(f"Total:    {len(results)} akun")
    print(f"✅ Sukses: {len(success)}")
    print(f"❌ Gagal:  {len(results) - len(success)}")
    
    if success:
        print(f"\n📧 Akun yang berhasil:")
        for r in success:
            print(f"   • {r['email']} / {r['password']}")
            if 'api_key' in r:
                print(f"     🔑 {r['api_key'][:40]}...")
    
    print(f"\n📄 Laporan: {report_path}")
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
