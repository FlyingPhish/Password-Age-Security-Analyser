# Password Age Security Analyser (PASSA)

A security analysis tool for Active Directory password ages and account activities. PASSA analyses password change patterns, account creation dates, and login activities to identify security risks and compliance issues. To be used with AD_Miner CSV outputs

```
================================================================================
SECURITY ANALYSIS REPORT
================================================================================

🌐 DOMAIN OVERVIEW
--------------------------------------------------------------------------------
Total Domains: 1
Total Accounts: 468

Domain Distribution:
• REDACTED.REDACTED: 468 accounts (100.0%)

🚨 CRITICAL FINDINGS:
• 6 accounts (1.3%) have passwords older than 20 years
• 20 accounts (4.3%) have passwords older than 15 years
• 132 accounts (28.2%) have never had their passwords changed
• 108 accounts (23.1%) haven't logged in for over 1 year
• 62 accounts (13.2%) have never logged in

📊 PASSWORD AGE METRICS:
• Average password age: 2.6 years
• Median password age: 0.3 years
• Oldest password: 24.6 years
• Newest password: 0.0 years

🕒 LAST LOGON METRICS:
• Average time since last logon: 1.4 years
• Median time since last logon: 0.0 years
• Longest time without logon: 17.2 years
• Most recent logon: 0.0 years ago

👤 ACCOUNT AGE METRICS:
• Average account age: 6.6 years
• Oldest account: 23.2 years
• Newest account: 0.0 years

📋 RECOMMENDED ACTIONS:
1. Immediate password resets required for:
   - All accounts with passwords over 20 years old (6 accounts)
   - All accounts with passwords over 15 years old (20 accounts)
   - All accounts with passwords over 1 year old
2. Account cleanup required:
   - Review 108 accounts inactive for over 1 year
   - Review 62 accounts that have never logged in
3. Implement or harden password policies:
   - Maximum password age: 90-180 days
   - Password complexity requirements
   - Enable password expiry
   - Use advanced password enforcers such as Entra Password Protection (Banned Passwords)
   - Account lockout threshold of 3-5 attempts
   - Locked Account Duration of 1 hour or ideally indefinite if culture and internal IT capabilities allow it.
   - Regular password audits
4. Review all 132 accounts that have never had password changes

📈 COMPLIANCE METRICS:
Based on recommendations of 90-180 day maximum password age:
• Compliant accounts (≤ 90 days): 228 (48.7%)
• Overdue for password change (> 90 days): 240 (51.3%)

Extended Compliance Metrics:
• Passwords > 1 year old: 179 (38.2%)
• Passwords > 2 years old: 146 (31.2%)

================================================================================

Detailed findings report has been saved to: output/detailed_findings.txt
Visualisation files have been saved to: output
```

## Sample Visulations
![image](https://github.com/user-attachments/assets/37da4b7c-bf62-48a3-acb8-e2c5cc61b6f5)

![image](https://github.com/user-attachments/assets/ba803fd2-e532-4bb1-af94-d826859afaf4)

## Features

- Password age analysis and statistics
- Account activity monitoring
- Multi-domain support
- Visual analytics (charts and graphs)
- Detailed security findings report
- Compliance metrics against recommendations

## Requirements

- Python 3.7+ (be smart, use the latest version 😉)
- Dependencies:
  ```
  pandas
  numpy
  matplotlib
  seaborn
  ```
- CSV of AD user information (I'd recommend using my fork of AD_Miner as it produces the CSV)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/FlyingPhish/Password-Statistics && cd Password-Statistics
   ```

2. Install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```bash
python passa.py -f data.csv
```

Specify output directory:
```bash
python passa.py -f data.csv -o /path/to/output
```

### Input CSV Format

Required columns:
- Domain
- Name
- Last Logon
- Last Password Change
- Account Creation Date

### Outputs

1. Security Analysis Report (console output)
   - Domain overview
   - Critical findings
   - Password age metrics
   - Login activity analysis
   - Compliance statistics

2. Visualisations (saved to output directory)
   - Password age distribution
   - Account vs password age scatter plot
   - Last logon distribution
   - Account creation timeline by domain
   - Age distribution by domain

3. Detailed Findings Report (text file)
   - Critical security issues
   - Account anomalies
   - Recommended actions
   - Compliance status

## Security Considerations

- Tool is designed for internal security audits
- Requires csv with details
