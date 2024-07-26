import requests
import time
from colorama import Fore, Style, init
from datetime import datetime
import json
import random
import os
import urllib.parse

# Inisialisasi colorama
init(autoreset=True)

# URL
get_url = "https://ranch-api.kuroro.com/api/Upgrades/GetPurchasableUpgrades"
buy_url = "https://ranch-api.kuroro.com/api/Upgrades/BuyUpgrade"
checkin_url = "https://ranch-api.kuroro.com/api/DailyStreak/ClaimDailyBonus"
mining_url = "https://ranch-api.kuroro.com/api/Clicks/MiningAndFeeding"
onboarding_url = "https://ranch-api.kuroro.com/api/Onboarding/CompleteOnboarding"
url_update_step = "https://ranch-api.kuroro.com/api/Onboarding/UpdateStep"
url_select_starter = "https://ranch-api.kuroro.com/api/Onboarding/SelectStarter"
url_hatch_egg = "https://ranch-api.kuroro.com/api/Onboarding/UpdateStep"
url_break_egg = "https://ranch-api.kuroro.com/api/Onboarding/UpdateStep"
get_daily_streak_state_url = "https://ranch-api.kuroro.com/api/DailyStreak/GetState"

# Fungsi untuk membaca token bearer dari file
def read_bearer_tokens(file_path):
    if not os.path.exists(file_path):
        print(Fore.RED + f"File {file_path} tidak ditemukan.")
        return [], True
    
    tokens = []
    invalid_lines = []
    
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('query_id=') or line.startswith('user='):
                tokens.append(line)
            else:
                invalid_lines.append(line)
    
    # Berikan peringatan jika file ada tetapi tidak mengandung token bearer yang valid
    if tokens:
        if invalid_lines:
            print(Fore.YELLOW + "Baris berikut tidak memenuhi format yang diharapkan:")
            for line in invalid_lines:
                print(Fore.YELLOW + f"  {line}")
    else:
        print(Fore.RED + "File data.txt tidak mengandung token bearer yang valid. Pastikan setiap baris dimulai dengan 'query_id=' atau 'user='.")
        return [], True

    return tokens, False

# Fungsi untuk membuat header untuk permintaan API
def create_headers(bearer_token):
    return {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://ranch.kuroro.com',
        'Pragma': 'no-cache',
        'Referer': 'https://ranch.kuroro.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; M2012K11AG Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, seperti Gecko) Version/4.0 Chrome/125.0.6422.165 Mobile',
        'Authorization': f'Bearer {bearer_token}'
    }

# Fungsi untuk melakukan tindakan dengan URL, nama tindakan, payload, dan token bearer yang diberikan
def perform_action(url, action_name, payload, bearer_token, silent=False):
    headers = create_headers(bearer_token)
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            if not silent:
                print(Fore.GREEN + f"🎉 {action_name}")
            return response
        else:
            if not silent and "Feeding" in action_name:
                print(Fore.RED + f"❌ Sudah Makan")
            elif not silent:
                print(Fore.RED + f"❌ {action_name} - Kode status: {response.status_code}")
            return response
    except requests.RequestException as e:
        if not silent:
            print(Fore.RED + f"Terjadi kesalahan selama {action_name}: {e}")
        return None

# Fungsi untuk menangani proses check-in
def checkin(bearer_token):
    # Tambahkan permintaan GET ke URL https://ranch-api.kuroro.com/api/DailyStreak/GetState
    headers = create_headers(bearer_token)
    try:
        state_response = requests.get(get_daily_streak_state_url, headers=headers)
        if state_response.status_code == 200:
            state_data = state_response.json()
            if not state_data['isTodayClaimed']:
                print(Fore.GREEN + "Successfully! You have not received the reward today.")
                current_date = datetime.now().strftime("%Y-%m-%d")
                payload = {"date": current_date}
                claim_response = requests.post(checkin_url, headers=headers, json=payload)
                if claim_response.status_code == 200:
                    claim_data = claim_response.json()
                    print(Fore.GREEN + f"{claim_data['message']}")
                else:
                    print(Fore.RED + "Reward already claimed today")
            else:
                print(Fore.GREEN + "Successfully! You have received the reward today.")
        else:
            print(Fore.RED + f"❌ Gagal mendapatkan daily streak state - Kode status: {state_response.status_code}")
    except requests.RequestException as e:
        print(Fore.RED + f"Terjadi kesalahan selama mendapatkan daily streak state: {e}")

# Fungsi untuk menangani proses upgrade
def upgrade_process(bearer_token):
    headers = create_headers(bearer_token)
    response = requests.get(get_url, headers=headers)

    if response.status_code == 200:
        upgrades = response.json()
        # Urutkan upgrade berdasarkan biaya dari yang terendah
        upgrades_sorted = sorted(upgrades, key=lambda x: x['cost'])
        for upgrade in upgrades_sorted:
            if upgrade['canBePurchased']:
                payload = {"upgradeId": upgrade['upgradeId']}
                purchase_response = requests.post(buy_url, json=payload, headers=headers)
                if purchase_response.status_code == 200:
                    print(Fore.GREEN + f"🎉 Upgrade Berhasil: {upgrade['name']}")
                else:
                    print(Fore.RED + f"❌ Upgrade Gagal: {upgrade['name']} - GOLD HABIS")
    else:
        print(Fore.RED + f"Permintaan gagal dengan kode status {response.status_code}")

# Fungsi untuk menangani langkah-langkah onboarding
def onboarding_sequence(bearer_token):
    print(Fore.CYAN + "Sedang menjalankan Tutorial...")
    # Update Step: Starter Selection
    payload = {"newStep": "StarterSelection"}
    perform_action(url_update_step, "Update to StarterSelection", payload, bearer_token, silent=True)
    time.sleep(1)
    
    # Select Starter Randomly
    starters = ["Ravolt", "Digby", "Toru"]
    selected_starter = random.choice(starters)
    payload = {"starterOption": selected_starter}
    response = perform_action(url_select_starter, f"Select Starter {selected_starter}", payload, bearer_token, silent=True)
    if response and response.status_code != 200:
        print(Fore.GREEN + "🎉 Sudah Melewati Tutorial")
    time.sleep(1)
    
    # Update Step: Tapping Egg
    payload = {"newStep": "TappingEgg"}
    perform_action(url_update_step, "Update to TappingEgg", payload, bearer_token, silent=True)
    time.sleep(1)
    
    # Hatch Egg
    response = perform_action(url_hatch_egg, "Hatch Egg", {}, bearer_token, silent=True)
    if response and response.status_code != 200:
        print(Fore.GREEN + "🎉 Sudah Melewati Tutorial")
    time.sleep(1)
    
    # Break Egg
    response = perform_action(url_break_egg, "Break Egg", {}, bearer_token, silent=True)
    if response and response.status_code != 200:
        print(Fore.GREEN + "🎉 Sudah Melewati Tutorial")
    time.sleep(1)
    
    # Update Step: Beast Hatched
    payload = {"newStep": "BeastHatched"}
    perform_action(url_update_step, "Update to BeastHatched", payload, bearer_token, silent=True)
    time.sleep(1)
    
    # New steps after BeastHatched
    new_steps = [
        "HelloBeast",
        "FeedBeast",
        "MoodXpExplanation",
        "PreMineShards",
        "MineShards",
        "FeedBeastAgain",
        "FeedBeastMore",
        "BeastLevelUp",
        "CoinSpendingUpgrades",
        "CoinEarningAway",
        "MoreLevelMoreCoins",
        "BeastHappinessAway",
        "BeastHappinessAway2",
        "ThatsAll"
    ]

    for step in new_steps:
        payload = {"newStep": step}
        perform_action(url_update_step, f"Update to {step}", payload, bearer_token, silent=True)
        time.sleep(1)

    # Complete Onboarding
    response = perform_action(onboarding_url, "Complete Onboarding", {}, bearer_token, silent=True)
    if response and response.status_code != 200:
        print(Fore.GREEN + "🎉 Sudah Melewati Tutorial")
    time.sleep(1)
    
    # Perform Mining and Feeding
    mining_and_feeding_payload = {"mineAmount": 0, "feedAmount": 5}
    perform_action(mining_url, "Mining and Feeding", mining_and_feeding_payload, bearer_token)
    time.sleep(1)

# Fungsi untuk mengekstrak username dari token
def extract_username(token):
    parsed_token = urllib.parse.unquote(token)
    start_index = parsed_token.find('user=')
    if (start_index == -1):
        print(Fore.RED + "Token tidak mengandung 'user='.")
        return "Unknown"

    end_index = parsed_token.find('&', start_index)
    if (end_index == -1):
        end_index = len(parsed_token)

    user_info = parsed_token[start_index + 5:end_index]

    try:
        user_json = json.loads(user_info)
        username = user_json.get('username', 'Unknown')
        return username
    except json.JSONDecodeError:
        # Coba untuk mengambil first_name jika JSON parsing gagal
        try:
            user_info = user_info.replace('%20', ' ')
            first_name_start = user_info.find('"first_name":"') + len('"first_name":"')
            first_name_end = user_info.find('"', first_name_start)
            first_name = user_info[first_name_start:first_name_end]
            return first_name
        except Exception:
            return 'Invalid JSON'

# Fungsi untuk mencetak pesan selamat datang
def print_welcome_message():
    print(Fore.GREEN + Style.BRIGHT + "BOT KURORANCH")
    print(Fore.WHITE + Style.BRIGHT + "BY   :" + Fore.CYAN + Style.BRIGHT + "@JerryM" + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "DONATE  :" + Fore.YELLOW + Style.BRIGHT + "0x6Fc6Ea113f38b7c90FF735A9e70AE24674E75D54" + Style.RESET_ALL)

# Fungsi untuk memproses semua akun
def process_accounts(user_choice, skip_tutorial, completed_accounts):
    bearer_tokens, warning_given = read_bearer_tokens('data.txt')
    
    if not bearer_tokens:
        if not warning_given:
            print(Fore.RED + "Tidak ada token bearer yang ditemukan. Pastikan file 'data.txt' ada dan tidak kosong.")
        return
    
    for i, bearer_token in enumerate(bearer_tokens, start=1):
        # Ekstrak dan tampilkan username
        username = extract_username(bearer_token)
        print(Fore.CYAN + f"👤 Memproses Akun {i} : {username}")
        
        if username not in completed_accounts and not skip_tutorial:
            onboarding_sequence(bearer_token)  # Pindah onboarding_sequence ke sini
            completed_accounts[username] = True
        
        checkin(bearer_token)
        
        mining_payload = {"mineAmount": 100, "feedAmount": 0}
        perform_action(mining_url, "Mining", mining_payload, bearer_token)
        
        feeding_payload = {"mineAmount": 0, "feedAmount": 1000}
        perform_action(mining_url, "Feeding", feeding_payload, bearer_token)

        if user_choice == 'y':
            upgrade_process(bearer_token)
        else:
            print(Fore.YELLOW + "Melewatkan proses upgrade untuk akun ini.")
        
        print(Fore.CYAN + Style.BRIGHT + f"\nAKUN {i} | {username} :" + Fore.GREEN + "DONE")
        time.sleep(5)
    
    print(Fore.RED + Style.BRIGHT + f"SEMUA AKUN TELAH DIPROSES")
    for _ in range(1800):
        minutes, seconds = divmod(1800 - _, 60)
        countdown_text = f"Recovering Energy {minutes} menit {seconds} detik"
        print(f"{countdown_text}", end="\r", flush=True)
        time.sleep(1)

# Fungsi utama
def main():
    print_welcome_message()
    
    user_choice = input(Fore.BLUE +  "Auto Upgrade? (y/n): ").strip().lower()
    if user_choice != 'y':
        user_choice = 'n'
    
    skip_tutorial = input(Fore.RED +  "Skip Tutorial? (y/n): ").strip().lower()
    if skip_tutorial != 'n':
        skip_tutorial = 'y'
    
    completed_accounts = {}
    
    while True:
        process_accounts(user_choice, skip_tutorial == 'y', completed_accounts)

if __name__ == "__main__":
    main()
