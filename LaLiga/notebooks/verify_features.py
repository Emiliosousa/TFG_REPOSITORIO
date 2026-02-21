import pandas as pd

def verify():
    df = pd.read_csv('../df_final_app.csv')
    cols = ['Date', 'HomeTeam', 'AwayTeam', 'Home_FIFA_Ova', 'Away_FIFA_Ova', 'Diff_FIFA_Ova', 'Home_Market_Value', 'Away_Market_Value', 'Log_Value_Diff']
    
    # Check if cols exist
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
        return

    print("✅ New Features Found.")
    print(df[cols].tail(10))
    
    # Check for excessive 75s (defaults)
    zeros = (df['Diff_FIFA_Ova'] == 0).sum()
    print(f"\nMatches with 0 Diff_FIFA_Ova: {zeros} / {len(df)}")
    
    # Check 2025 data specifically
    df['Date'] = pd.to_datetime(df['Date'])
    recent = df[df['Date'] > '2024-08-01']
    print("\n--- 2025 Data Sample ---")
    print(recent[cols].head(5))

if __name__ == '__main__':
    verify()
