# THM-HAMMER
Malware analysis and threat-intelligence CTF from TryHackMe’s “Friday Overtime.” Includes SHA1 validation, framework correlation, MITRE ATT&amp;CK mapping, and OSINT pivots by Slade Venter.


# TryHackMe – HAMMER
Author: Slade Venter

Category: Web Application Security / Authentication / JWT Tokens

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
  -SSH on port [22]
  -PHP web server on port [1337]

  **nmap -sC -sV -p- <hammer.thm>**
  ![Nmap Scan](screenshots/nmapresults.png) 

# Directory Enumeration & Password Reset Analysis
Using Feroxbuster, directory enumeration was performed against the web server. Modified dirb wordlists were used. 


feroxbuster -u http://hammer.thm:1337 -w <wordlist>
![Directory Enumeration](./screenshots/02_directory_enum.png)

This HMR discovery allows use to modifiy the dirb wordlist in a seperate directory to the scan spefically for HMR.

![Directory Enumeration](./screenshots/02_directory_enum.png)
An error directory was discovered that showed evidence of previous password reset attempts. This revealed the existence of a password recovery mechanism for:
