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
  
  ![Nmap Scan](./screenshots/1._nmap_results.png) 
