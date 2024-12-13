import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
import os
import textwrap
import re

class PasswordAgeAnalyser:
    def __init__(self, csv_path):
        """Initialise with path to CSV file."""
        try:
            self.df = pd.read_csv(csv_path)
            required_columns = ["Domain", "Name", "Last Logon", "Last Password Change", "Account Creation Date"]
            if not all(col in self.df.columns for col in required_columns):
                raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            sys.exit(1)
            
        self.processed_df = None

    def _parse_time_string(self, time_str):
        """Convert time string format to decimal years using regex."""
        try:
            # Handle "Never" case
            if time_str == "Never":
                return None
                
            # Handle case where there's no year part
            if not 'year' in time_str:
                parts = re.match(r'(\d+)\s*months?\s*and\s*(\d+)\s*days?', time_str)
                if parts:
                    months = int(parts.group(1))
                    days = int(parts.group(2))
                    return months/12 + days/365
                # Handle case with just days
                days_only = re.match(r'(\d+)\s*days?', time_str)
                if days_only:
                    return int(days_only.group(1))/365
                return None

            # Parse with years
            pattern = r'(\d+)\s*years?,\s*(\d+)\s*months?\s*and\s*(\d+)\s*days?|(\d+)\s*year,\s*(\d+)\s*months?\s*and\s*(\d+)\s*days?'
            match = re.match(pattern, time_str)
            
            if match:
                # Check which group matched (plural or singular)
                if match.group(1) is not None:
                    years = int(match.group(1))
                    months = int(match.group(2))
                    days = int(match.group(3))
                else:
                    years = int(match.group(4))
                    months = int(match.group(5))
                    days = int(match.group(6))
                
                return years + (months/12) + (days/365)
            
            return None
        except Exception as e:
            print(f"Error parsing time string: {time_str}")
            print(f"Error details: {str(e)}")
            return None

    def process_data(self):
        """Process the raw data and add calculated columns."""
        # Create copy of dataframe
        self.processed_df = self.df.copy()
        
        # Count "Never" logged in before conversion
        self.never_logged_in = len(self.df[self.df['Last Logon'] == "Never"])
        
        # Count passwords never changed (exact string match)
        self.never_changed_password = len(self.df[
            self.df['Last Password Change'] == self.df['Account Creation Date']
        ])
        
        # Debug print
        # print("\nDEBUG: Accounts that have never changed their password:")
        never_changed = self.df[self.df['Last Password Change'] == self.df['Account Creation Date']]
        for _, row in never_changed.iterrows():
            print(f"  - {row['Name']}: Created: {row['Account Creation Date']}, Last Changed: {row['Last Password Change']}")
        
        # Convert time strings to decimal years
        self.processed_df['password_age_decimal'] = self.processed_df['Last Password Change'].apply(self._parse_time_string)
        self.processed_df['account_age_decimal'] = self.processed_df['Account Creation Date'].apply(self._parse_time_string)
        self.processed_df['last_logon_decimal'] = self.processed_df['Last Logon'].apply(self._parse_time_string)
        
        # Calculate differences
        self.processed_df['age_difference'] = self.processed_df['account_age_decimal'] - self.processed_df['password_age_decimal']
        self.processed_df['logon_age'] = self.processed_df['last_logon_decimal']
        
        return self.processed_df

    def generate_statistics(self):
        """Generate comprehensive statistics about the data."""
        if self.processed_df is None:
            self.process_data()
            
        stats = {
            'password_age': {
                'average': self.processed_df['password_age_decimal'].mean(),
                'median': self.processed_df['password_age_decimal'].median(),
                'oldest': self.processed_df['password_age_decimal'].max(),
                'newest': self.processed_df['password_age_decimal'].min(),
                'std_dev': self.processed_df['password_age_decimal'].std(),
                'over_90days': len(self.processed_df[self.processed_df['password_age_decimal'] > 0.25]),
                'over_1year': len(self.processed_df[self.processed_df['password_age_decimal'] > 1]),
                'over_2years': len(self.processed_df[self.processed_df['password_age_decimal'] > 2]),
                'over_15_years': len(self.processed_df[self.processed_df['password_age_decimal'] > 15]),
                'over_20_years': len(self.processed_df[self.processed_df['password_age_decimal'] > 20]),
                'under_90days': len(self.processed_df[self.processed_df['password_age_decimal'] <= 0.25])
            },
            'account_age': {
                'average': self.processed_df['account_age_decimal'].mean(),
                'median': self.processed_df['account_age_decimal'].median(),
                'oldest': self.processed_df['account_age_decimal'].max(),
                'newest': self.processed_df['account_age_decimal'].min(),
                'std_dev': self.processed_df['account_age_decimal'].std()
            },
            'last_logon': {
                'average': self.processed_df['logon_age'].mean(),
                'median': self.processed_df['logon_age'].median(),
                'oldest': self.processed_df['logon_age'].max(),
                'newest': self.processed_df['logon_age'].min(),
                'over_90days': len(self.processed_df[self.processed_df['logon_age'] > 0.25]),
                'over_1year': len(self.processed_df[self.processed_df['logon_age'] > 1]),
                'never_logged': self.never_logged_in
            },
            'general': {
                'total_accounts': len(self.processed_df),
                'total_domains': len(self.processed_df['Domain'].unique()),
                'average_age_difference': self.processed_df['age_difference'].mean(),
                'max_age_difference': self.processed_df['age_difference'].max(),
                'accounts_never_changed': self.never_changed_password  # Use exact string match count
            },
            'domains': {
                'distribution': self.processed_df['Domain'].value_counts().to_dict()
            }
        }
        
        return stats
    
    def generate_visualisations(self, output_dir='./'):
        """Generate visualisations of the data."""
        if self.processed_df is None:
            self.process_data()
            
        # Use default style instead of seaborn
        plt.style.use('default')
        
        # Password Age Distribution
        plt.figure(figsize=(12, 6))
        valid_passwords = self.processed_df['password_age_decimal'].dropna()
        plt.hist(valid_passwords, bins=min(20, len(valid_passwords)//10), edgecolor='black')
        plt.title('Distribution of Password Ages')
        plt.xlabel('Password Age (Years)')
        plt.ylabel('Count')
        plt.savefig(os.path.join(output_dir, 'password_age_distribution.png'))
        plt.close()
        
        # Account vs Password Age Scatter
        plt.figure(figsize=(12, 6))
        valid_data = self.processed_df.dropna(subset=['account_age_decimal', 'password_age_decimal'])
        plt.scatter(valid_data['account_age_decimal'], 
                   valid_data['password_age_decimal'],
                   alpha=0.5)
        max_age = max(valid_data['account_age_decimal'].max(), valid_data['password_age_decimal'].max())
        plt.plot([0, max_age], [0, max_age], 'r--', alpha=0.5, label='Password Age = Account Age')
        plt.title('Account Age vs Password Age')
        plt.xlabel('Account Age (Years)')
        plt.ylabel('Password Age (Years)')
        plt.legend()
        plt.savefig(os.path.join(output_dir, 'account_vs_password_age.png'))
        plt.close()
        
        # Last Logon Distribution
        plt.figure(figsize=(12, 6))
        valid_logons = self.processed_df['last_logon_decimal'].dropna()
        if len(valid_logons) > 0:
            plt.hist(valid_logons, bins=min(20, len(valid_logons)//10), edgecolor='black')
            plt.title('Distribution of Last Logon Times')
            plt.xlabel('Time Since Last Logon (Years)')
            plt.ylabel('Count')
            plt.savefig(os.path.join(output_dir, 'last_logon_distribution.png'))
        plt.close()
        
        # Timeline of Account Creations by Domain
        plt.figure(figsize=(15, 8))
        
        # Sort the dataframe by account age (oldest first)
        timeline_data = self.processed_df.sort_values('account_age_decimal', ascending=True)
        
        # Create a cumulative count for each domain
        domains = timeline_data['Domain'].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(domains)))  # Different color for each domain
        
        for domain, color in zip(domains, colors):
            domain_data = timeline_data[timeline_data['Domain'] == domain]
            # Create cumulative count
            x = domain_data['account_age_decimal']
            y = range(1, len(domain_data) + 1)
            plt.plot(x, y, label=domain, color=color, linewidth=2)
            
            # Add markers for significant points
            plt.scatter(x, y, color=color, alpha=0.5)
        
        plt.title('Timeline of Account Creations by Domain')
        plt.xlabel('Years Ago')
        plt.ylabel('Cumulative Number of Accounts')
        
        # Add grid for better readability
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Customise legend
        plt.legend(title='Domains', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout to prevent legend cutoff
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, 'account_creation_timeline.png'), 
                    bbox_inches='tight',
                    dpi=300)
        plt.close()

        # Optional: Add a stacked bar chart showing account age distribution by domain
        plt.figure(figsize=(15, 8))
        
        # Create age brackets
        bins = [0, 0.25, 1, 2, 5, 10, 15, 20, float('inf')]
        labels = ['<90 days', '90d-1yr', '1-2yr', '2-5yr', '5-10yr', '10-15yr', '15-20yr', '>20yr']
        
        timeline_data['age_bracket'] = pd.cut(timeline_data['account_age_decimal'], 
                                            bins=bins, 
                                            labels=labels)
        
        # Create pivot table
        pivot_data = pd.crosstab(timeline_data['Domain'], timeline_data['age_bracket'])
        
        # Create stacked bar chart
        pivot_data.plot(kind='bar', stacked=True, figsize=(15, 8))
        plt.title('Account Age Distribution by Domain')
        plt.xlabel('Domain')
        plt.ylabel('Number of Accounts')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add grid for better readability
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        plt.savefig(os.path.join(output_dir, 'account_age_distribution_by_domain.png'),
                    bbox_inches='tight',
                    dpi=300)
        plt.close()

    def generate_detailed_report(self, output_dir='./'):
        """Generate a detailed report of findings by category."""
        if self.processed_df is None:
            self.process_data()
            
        report_path = os.path.join(output_dir, 'detailed_findings.txt')
        
        with open(report_path, 'w') as f:
            f.write("DETAILED SECURITY FINDINGS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Critical Age Findings
            f.write("CRITICAL PASSWORD AGE FINDINGS\n")
            f.write("-" * 30 + "\n")
            
            # Over 20 years
            f.write("\n1. Accounts with passwords over 20 years old:\n")
            over_20 = self.processed_df[self.processed_df['password_age_decimal'] > 20]
            if len(over_20) > 0:
                for _, row in over_20.iterrows():
                    f.write(f"   - {row['Name']}\n")
                    f.write(f"     Last Changed: {row['Last Password Change']}\n")
                    f.write(f"     Account Created: {row['Account Creation Date']}\n")
                    f.write(f"     Last Logon: {row['Last Logon']}\n\n")
            else:
                f.write("   None found\n\n")
            
            # Over 15 years
            f.write("\n2. Accounts with passwords over 15 years old:\n")
            over_15 = self.processed_df[self.processed_df['password_age_decimal'] > 15]
            if len(over_15) > 0:
                for _, row in over_15.iterrows():
                    f.write(f"   - {row['Name']}\n")
                    f.write(f"     Last Changed: {row['Last Password Change']}\n")
                    f.write(f"     Account Created: {row['Account Creation Date']}\n")
                    f.write(f"     Last Logon: {row['Last Logon']}\n\n")
            else:
                f.write("   None found\n\n")
            
            # Never Changed Password
            f.write("\nPASSWORD NEVER CHANGED\n")
            f.write("-" * 30 + "\n")
            never_changed = self.df[self.df['Last Password Change'] == self.df['Account Creation Date']]
            if len(never_changed) > 0:
                for _, row in never_changed.iterrows():
                    f.write(f"   - {row['Name']}\n")
                    f.write(f"     Account Created: {row['Account Creation Date']}\n")
                    f.write(f"     Last Logon: {row['Last Logon']}\n\n")
            else:
                f.write("   None found\n\n")
            
            # Logon Issues
            f.write("\nLOGON ISSUES\n")
            f.write("-" * 30 + "\n")
            
            # Never Logged In
            f.write("\n1. Accounts that have never logged in:\n")
            never_logged = self.df[self.df['Last Logon'] == "Never"]
            if len(never_logged) > 0:
                for _, row in never_logged.iterrows():
                    f.write(f"   - {row['Name']}\n")
                    f.write(f"     Account Created: {row['Account Creation Date']}\n")
                    f.write(f"     Last Password Change: {row['Last Password Change']}\n\n")
            else:
                f.write("   None found\n\n")
            
            # No Login for Over 1 Year
            f.write("\n2. Accounts inactive for over 1 year:\n")
            inactive = self.processed_df[self.processed_df['logon_age'] > 1]
            if len(inactive) > 0:
                for _, row in inactive.iterrows():
                    if pd.notna(row['logon_age']):  # Exclude "Never" logged in accounts
                        f.write(f"   - {row['Name']}\n")
                        f.write(f"     Last Logon: {row['Last Logon']}\n")
                        f.write(f"     Account Created: {row['Account Creation Date']}\n")
                        f.write(f"     Last Password Change: {row['Last Password Change']}\n\n")
            else:
                f.write("   None found\n\n")
            
            # Recommendations
            f.write("\nRECOMMENDED ACTIONS\n")
            f.write("-" * 30 + "\n")
            f.write("\n1. Immediate Actions Required:\n")
            f.write("   - Reset passwords for all accounts listed in the '20+ years' section\n")
            f.write("   - Review and reset passwords for accounts in the '15+ years' section\n")
            f.write("   - Review and reset passwords for accounts with passwords over 1 year old\n")
            f.write("   - Review all accounts that have never had their passwords changed\n\n")
            
            f.write("2. Account Cleanup:\n")
            f.write("   - Review and consider disabling accounts that have never logged in\n")
            f.write("   - Audit accounts inactive for over 1 year\n")
            f.write("   - Consider implementing automatic account disable after 90 days of inactivity\n\n")
            
            f.write("3. Policy Recommendations:\n")
            f.write("   - Implement maximum password age of 90-180 days\n")
            f.write("   - Enable password complexity requirements\n")
            f.write("   - Enable password expiry\n")
            f.write("   - Account lockout threshold of 3-5 attempts\n")
            f.write("   - Locked Account Duration of 1 hour or ideally indefinite if culture and internal IT capabilities allow it.\n")
            f.write("   - Use advanced password enforcers such as Entra Password Protection (Banned Passwords)\n")
            f.write("   - Regular password audits\n")
            f.write("   - Regular account activity audits\n\n")
            
            # Summary
            f.write("\nSUMMARY OF FINDINGS\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Accounts Analysed: {len(self.df)}\n")
            f.write(f"Accounts with passwords > 20 years: {len(over_20)}\n")
            f.write(f"Accounts with passwords > 15 years: {len(over_15)}\n")
            f.write(f"Accounts that never changed password: {len(never_changed)}\n")
            f.write(f"Accounts that never logged in: {len(never_logged)}\n")
            f.write(f"Accounts inactive > 1 year: {len(inactive)}\n")

        print(f"\nDetailed findings report has been saved to: {report_path}")

def print_security_report(stats):
    """Print a detailed security report with risk assessments."""
    total_accounts = stats['general']['total_accounts']
    
    print("\n" + "="*80)
    print("SECURITY ANALYSIS REPORT")
    print("="*80)
    
    print("\n🌐 DOMAIN OVERVIEW")
    print("-"*80)
    print(f"Total Domains: {stats['general']['total_domains']}")
    print(f"Total Accounts: {stats['general']['total_accounts']}")
    print("\nDomain Distribution:")
    for domain, count in stats['domains']['distribution'].items():
        print(f"• {domain}: {count} accounts ({(count/stats['general']['total_accounts']*100):.1f}%)")
    
    print("\n🚨 CRITICAL FINDINGS:")
    print(f"• {stats['password_age']['over_20_years']} accounts ({(stats['password_age']['over_20_years']/total_accounts*100):.1f}%) have passwords older than 20 years")
    print(f"• {stats['password_age']['over_15_years']} accounts ({(stats['password_age']['over_15_years']/total_accounts*100):.1f}%) have passwords older than 15 years")
    print(f"• {stats['general']['accounts_never_changed']} accounts ({(stats['general']['accounts_never_changed']/total_accounts*100):.1f}%) have never had their passwords changed")
    print(f"• {stats['last_logon']['over_1year']} accounts ({(stats['last_logon']['over_1year']/total_accounts*100):.1f}%) haven't logged in for over 1 year")
    print(f"• {stats['last_logon']['never_logged']} accounts ({(stats['last_logon']['never_logged']/total_accounts*100):.1f}%) have never logged in")
    
    print("\n📊 PASSWORD AGE METRICS:")
    print(f"• Average password age: {stats['password_age']['average']:.1f} years")
    print(f"• Median password age: {stats['password_age']['median']:.1f} years")
    print(f"• Oldest password: {stats['password_age']['oldest']:.1f} years")
    print(f"• Newest password: {stats['password_age']['newest']:.1f} years")
    
    print("\n🕒 LAST LOGON METRICS:")
    print(f"• Average time since last logon: {stats['last_logon']['average']:.1f} years")
    print(f"• Median time since last logon: {stats['last_logon']['median']:.1f} years")
    print(f"• Longest time without logon: {stats['last_logon']['oldest']:.1f} years")
    print(f"• Most recent logon: {stats['last_logon']['newest']:.1f} years ago")
    
    print("\n👤 ACCOUNT AGE METRICS:")
    print(f"• Average account age: {stats['account_age']['average']:.1f} years")
    print(f"• Oldest account: {stats['account_age']['oldest']:.1f} years")
    print(f"• Newest account: {stats['account_age']['newest']:.1f} years")
    
    # print("\n⚠️ RISK ASSESSMENT:")
    # risk_level = "HIGH"
    # if (stats['password_age']['over_20_years'] == 0 and 
    #     stats['password_age']['over_15_years'] < 5 and 
    #     stats['last_logon']['over_1year'] < total_accounts * 0.1):  # Less than 10% inactive
    #     risk_level = "MEDIUM"
    # if (stats['password_age']['over_15_years'] == 0 and 
    #     stats['password_age']['average'] < 1 and 
    #     stats['last_logon']['over_90days'] < total_accounts * 0.05):  # Less than 5% inactive
    #     risk_level = "LOW"
        
    # print(f"Overall Risk Level: {risk_level}")
    
    print("\n📋 RECOMMENDED ACTIONS:")
    print("1. Immediate password resets required for:")
    print(f"   - All accounts with passwords over 20 years old ({stats['password_age']['over_20_years']} accounts)")
    print(f"   - All accounts with passwords over 15 years old ({stats['password_age']['over_15_years']} accounts)")
    print(f"   - All accounts with passwords over 1 year old")
    print("2. Account cleanup required:")
    print(f"   - Review {stats['last_logon']['over_1year']} accounts inactive for over 1 year")
    print(f"   - Review {stats['last_logon']['never_logged']} accounts that have never logged in")
    print("3. Implement or harden password policies:")
    print("   - Maximum password age: 90-180 days")
    print("   - Password complexity requirements")
    print("   - Enable password expiry")
    print("   - Use advanced password enforcers such as Entra Password Protection (Banned Passwords)")
    print("   - Account lockout threshold of 3-5 attempts")
    print("   - Locked Account Duration of 1 hour or ideally indefinite if culture and internal IT capabilities allow it.")
    print("   - Regular password audits")
    print(f"4. Review all {stats['general']['accounts_never_changed']} accounts that have never had password changes")
    
    print("\n📈 COMPLIANCE METRICS:")
    print("Based on recommendations of 90-180 day maximum password age:")
    print(f"• Compliant accounts (≤ 90 days): {stats['password_age']['under_90days']} ({(stats['password_age']['under_90days']/total_accounts*100):.1f}%)")
    print(f"• Overdue for password change (> 90 days): {stats['password_age']['over_90days']} ({(stats['password_age']['over_90days']/total_accounts*100):.1f}%)")
    print("\nExtended Compliance Metrics:")
    print(f"• Passwords > 1 year old: {stats['password_age']['over_1year']} ({(stats['password_age']['over_1year']/total_accounts*100):.1f}%)")
    print(f"• Passwords > 2 years old: {stats['password_age']['over_2years']} ({(stats['password_age']['over_2years']/total_accounts*100):.1f}%)")
    
    print("\n" + "="*80)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyse password and account age data from CSV file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Example usage:
                python passa.py -f data.csv
                python passa.py --file data.csv --output results/
            
            CSV file should contain columns:
                - Domain
                - Name
                - Last Logon
                - Last Password Change
                - Account Creation Date
        ''')
    )
    
    parser.add_argument('-f', '--file', 
                        required=True,
                        help='Path to the input CSV file')
    
    parser.add_argument('-o', '--output',
                        default='output',
                        help='Output directory for results (default: output)')
    
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()
    
    try:
        # Initialise analyser
        print(f"Reading file: {args.file}")
        analyser = PasswordAgeAnalyser(args.file)
        
        # Process data
        processed_data = analyser.process_data()
        
        # Generate statistics
        stats = analyser.generate_statistics()
        
        # Print detailed security report
        print_security_report(stats)
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Generate visualisations
        analyser.generate_visualisations(args.output)

        # Generate detailed findings report
        analyser.generate_detailed_report(args.output)
        
        print(f"\nVisualisation files have been saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
