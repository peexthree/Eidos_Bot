import os

# =============================================================================
# 1. ТЕХНИЧЕСКИЙ СТАТУС
# =============================================================================
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://eidos-bot-n5oo.onrender.com')
DATABASE_URL = os.environ.get('DATABASE_URL')
try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID'))
except (TypeError, ValueError):
    ADMIN_ID = None
CHANNEL_ID = "@Eidos_Chronicles"
BOT_USERNAME = "Eidos_Interface_bot"

MENU_IMAGE_URL = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/A_welcome_menu_202602132051.jpeg"
MENU_IMAGE_URL_MONEY = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/main.jpeg"
MENU_IMAGE_URL_MIND = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/mind.jpeg"
MENU_IMAGE_URL_TECH = "https://raw.githubusercontent.com/peexthree/Eidos_Bot/main/neuro.jpeg"
MENU_IMAGE_URL_ARCHITECT = "AgACAgIAAyEFAATh7MR7AAPWaaY38d-H5Q9abb0uQEPoL_PM630AAvQUaxt6SzBJSYSr4t0c-K4BAAMCAAN5AAM6BA"

MENU_IMAGES = {
    "get_protocol": "AgACAgIAAyEFAATh7MR7AAMbaZiXWWBNZFSn6X6X2jOioZMcD4IAAtUZaxvxO8lIK-8ENhRiRO4BAAMCAAN5AAM6BA",
    "get_signal": "AgACAgIAAyEFAATh7MR7AAMcaZia1meLvNIXtxC31naYVRUdU0UAAusZaxvxO8lInbWGVkVPCzMBAAMCAAN5AAM6BA",
    "zero_layer_menu": "AgACAgIAAyEFAATh7MR7AAMdaZia3Mvn9Ei9sORXsrT7JqVdiJoAAuwZaxvxO8lIV15auH4uEggBAAMCAAN5AAM6BA",
    "shop_menu": "AgACAgIAAyEFAATh7MR7AAMeaZia316nKfu5np_DHUysBTP3Sr8AAu0ZaxvxO8lIn6oxjBv0ffoBAAMCAAN5AAM6BA",
    "inventory": "AgACAgIAAyEFAATh7MR7AAMfaZia6HF2HjKG5ePc8AHXDiejj7YAAu4ZaxvxO8lIeVpyAAFVrl-yAQADAgADeQADOgQ",
    "shadow_shop_menu": "AgACAgIAAyEFAATh7MR7AANFaZni1ubFAosjGziRaywsdKJ_9yAAAkoXaxtY9NFI3b48v4UAAfkHAQADAgADeQADOgQ",
    "leaderboard": "AgACAgIAAyEFAATh7MR7AAMgaZia67bwFejOVI1_f_0oGaRwRdIAAu8ZaxvxO8lIGaXlnbg6wfIBAAMCAAN5AAM6BA",
    "referral": "AgACAgIAAyEFAATh7MR7AAMhaZia7XFH1DEcGKFicao3VG9AGrIAAvAZaxvxO8lIL4E1Iz8pCkQBAAMCAAN5AAM6BA",
    "diary_menu": "AgACAgIAAyEFAATh7MR7AAMiaZia77GYlpexeczG3gQ_GldaPicAAvEZaxvxO8lIyNFPQ2k3xqoBAAMCAAN5AAM6BA",
    "guide": "AgACAgIAAyEFAATh7MR7AAMjaZia8MBMuD9XL6kEynvbsw5D_dQAAvIZaxvxO8lIFOmwKmnsucEBAAMCAAN5AAM6BA",
    "admin_panel": "AgACAgIAAyEFAATh7MR7AAMkaZia834CgWuumHCALV2OojtSdJcAAvMZaxvxO8lITSVj78T2dxIBAAMCAAN5AAM6BA",
    "pvp_menu": "AgACAgIAAyEFAATh7MR7AANKaZpNXxQ04fY5LOi_8OhKaY8l-3QAAisRaxtY9NlI1M0RzvtStkIBAAMCAAN5AAM6BA"
}

ITEM_IMAGES = {
    "rusty_knife": "AgACAgIAAyEFAATh7MR7AANLaZpeggTtfzumT7lXOJ7Xhh9nTWcAAkkRaxtY9NlIYRPEt1hm6lEBAAMCAAN5AAM6BA",
    "crowbar": "AgACAgIAAyEFAATh7MR7AANMaZpehW8iaqb0ewjaZnXzJ7_fRPIAAkoRaxtY9NlIYvkAAbI5DbkrAQADAgADeQADOgQ",
    "data_bat": "AgACAgIAAyEFAATh7MR7AANNaZpeiGjY9k3cadHHoGaqUJZLmcQAAksRaxtY9NlI2Rvp9pxyFlUBAAMCAAN5AAM6BA",
    "shock_baton": "AgACAgIAAyEFAATh7MR7AANOaZpeibthtThAgn2uVZAFV1oyuYIAAkwRaxtY9NlI0FXdlvZfziQBAAMCAAN5AAM6BA",
    "cyber_katana": "AgACAgIAAyEFAATh7MR7AANPaZpejOSnoEku7TfKzppKd2ZCJnYAAk0RaxtY9NlIZ_wmrKtwiPMBAAMCAAN5AAM6BA",
    "laser_pistol": "AgACAgIAAyEFAATh7MR7AANQaZpejszTRaExnwjp8PjKGKtMGUYAAk8RaxtY9NlIPcKvIur6tgQBAAMCAAN5AAM6BA",
    "plasma_rifle": "AgACAgIAAyEFAATh7MR7AANRaZpekLKgSJ2fszdsQwJbBbSggd4AAlARaxtY9NlI5BUgiuKN7TABAAMCAAN5AAM6BA",
    "nano_blade": "AgACAgIAAyEFAATh7MR7AANSaZpekYRWtbp5rjZP5p9Dwn6OhjUAAlERaxtY9NlIECPPULBWhPYBAAMCAAN5AAM6BA",
    "void_cannon": "AgACAgIAAyEFAATh7MR7AANTaZpek4vTZ04rd3nJz6SmI7dPQOgAAlIRaxtY9NlIrLHVdqyTiRUBAAMCAAN5AAM6BA",
    "singularity_sword": "AgACAgIAAyEFAATh7MR7AANUaZpeld7C570jAiivbLLjkqaOFUMAAlMRaxtY9NlIjaOBAyrTvWEBAAMCAAN5AAM6BA",
    "nomad_goggles": "AgACAgIAAyEFAATh7MR7AANVaZpelz6nZoeYwMjvVf75PnVSI8MAAlQRaxtY9NlIQ9iUZfOy6yABAAMCAAN5AAM6BA",
    "scavenger_mask": "AgACAgIAAyEFAATh7MR7AANWaZpemViO8x3LWY1jqEnLVGktGwYAAlURaxtY9NlI-nu3G8lnmz0BAAMCAAN5AAM6BA",
    "tactical_helmet": "AgACAgIAAyEFAATh7MR7AANXaZpemw3J50khhmhmzAIvMl2PKgMAAlYRaxtY9NlIXc77N3JZn-YBAAMCAAN5AAM6BA",
    "vampire_visor": "AgACAgIAAyEFAATh7MR7AANYaZpenBndfv4j1TU35Snpxvj8dGoAAlcRaxtY9NlI4AMagQwiE9kBAAMCAAN5AAM6BA",
    "cyber_halo": "AgACAgIAAyEFAATh7MR7AANZaZpenueeiH79KsJOT8ECVK1CUAMAAlgRaxtY9NlIMusjZPhBhT4BAAMCAAN5AAM6BA",
    "overclock_crown": "AgACAgIAAyEFAATh7MR7AANaaZpeoE4Z0RZj45bKEvBVjCgaooAAAlkRaxtY9NlIOAzypF3H6oIBAAMCAAN5AAM6BA",
    "void_walker_hood": "AgACAgIAAyEFAATh7MR7AANbaZpeoUdJAAHqDjFVcKSzLlfzankZAAJaEWsbWPTZSBwsV7pkJMvQAQADAgADeQADOgQ",
    "architect_mask": "AgACAgIAAyEFAATh7MR7AANcaZpeo5USxhMxS9tEiynVd8QWfkAAAlsRaxtY9NlIdWxrveZGL5gBAAMCAAN5AAM6BA",
    "relic_vampire": "AgACAgIAAyEFAATh7MR7AANdaZpepKvSLu3IJxXZYBEETOCT4iEAAlwRaxtY9NlIGc1weVsTjj4BAAMCAAN5AAM6BA",
    "relic_speed": "AgACAgIAAyEFAATh7MR7AANeaZpepvlPZcq8dnO3RlZiiMVmhOkAAl0RaxtY9NlI87pBLEevHNYBAAMCAAN5AAM6BA",
    "hoodie": "AgACAgIAAyEFAATh7MR7AANgaZpeqY7pOGcGJjM1s5sJCpiHgq8AAl8RaxtY9NlIx4eLmXRYvrYBAAMCAAN5AAM6BA",
    "leather_jacket": "AgACAgIAAyEFAATh7MR7AANhaZpeq-4bzxu4kovk32kfveOamPQAAmARaxtY9NlIIbBoCZHChGMBAAMCAAN5AAM6BA",
    "kevlar_vest": "AgACAgIAAyEFAATh7MR7AANfaZpeqK_ZFrGlAAEgmahBj63Il_aSAAJeEWsbWPTZSMXeZ_IMvB6MAQADAgADeQADOgQ",
    "tactical_suit": "AgACAgIAAyEFAATh7MR7AANiaZpereWauvj3R_wbILSQvZPLNbwAAmERaxtY9NlI5fjV07b70f8BAAMCAAN5AAM6BA",
    "exo_skeleton": "AgACAgIAAyEFAATh7MR7AANjaZper-gzmBWi9WNamolL_sQtgsoAAmIRaxtY9NlIeG4uc5NwZF8BAAMCAAN5AAM6BA",
    "nano_suit": "AgACAgIAAyEFAATh7MR7AANkaZpesKEB5h6QlkWubHU-jwEe6vwAAmMRaxtY9NlISvq219LQazkBAAMCAAN5AAM6BA",
    "phantom_cloak": "AgACAgIAAyEFAATh7MR7AANlaZpeskeH8vwAATwD8js5Osa2DNCPAAJkEWsbWPTZSJpf3bKz_r2MAQADAgADeQADOgQ",
    "force_field": "AgACAgIAAyEFAATh7MR7AANmaZpes94RfR9iVpvNKc_mgVkFOssAAmURaxtY9NlI_C8lwtu15bgBAAMCAAN5AAM6BA",
    "reality_armor": "AgACAgIAAyEFAATh7MR7AANnaZpetU7WAi4d3fouA9_ePPEOFGUAAmYRaxtY9NlIA2-Lnj4q2FsBAAMCAAN5AAM6BA",
    "quantum_shield": "AgACAgIAAyEFAATh7MR7AANoaZpet8noqjtScI3Rtgf8ok3sSMYAAmcRaxtY9NlITlH2AnSDZ_gBAAMCAAN5AAM6BA",
    "ram_chip": "AgACAgIAAyEFAATh7MR7AANpaZpeuWxSrSOthxYzUUQc7h7SylAAAmgRaxtY9NlINEXH8eOiQBUBAAMCAAN5AAM6BA",
    "cpu_booster": "AgACAgIAAyEFAATh7MR7AANqaZpeurqUmLoz6H2szPMZb4ThAAHeAAJpEWsbWPTZSLrB1tuT94rkAQADAgADeQADOgQ",
    "ai_core": "AgACAgIAAyEFAATh7MR7AANraZpevD2RZn592VWghvs4xK8NvjsAAmoRaxtY9NlI91oHfhiiKE8BAAMCAAN5AAM6BA",
    "neural_link": "AgACAgIAAyEFAATh7MR7AANsaZpevVNfEsaNzY_iqlLhk4dXGYsAAmsRaxtY9NlIxDRxTUouRLgBAAMCAAN5AAM6BA",
    "chronometer": "AgACAgIAAyEFAATh7MR7AANtaZpev4F2AcWxo5R2VChByv3PXCwAAmwRaxtY9NlIYXbBcwvUfogBAAMCAAN5AAM6BA",
    "god_mode_chip": "AgACAgIAAyEFAATh7MR7AANuaZpewOKtgW2X6ctdUFKY2S8f5p8AAm0RaxtY9NlIejZFGPhU4-cBAAMCAAN5AAM6BA",
    "glitch_filter": "AgACAgIAAyEFAATh7MR7AANvaZpewox3R77MJ2bDbGtz-4MVLoQAAm4RaxtY9NlIWc6GPPSrpSoBAAMCAAN5AAM6BA",
    "overclocker": "AgACAgIAAyEFAATh7MR7AANwaZpew4y4wVmP59XQIIZ150sEdjwAAm8RaxtY9NlIN6qORwXX4WEBAAMCAAN5AAM6BA",
    "backup_drive": "AgACAgIAAyEFAATh7MR7AANxaZpexpNH5-ojsMfxYlJxsqBtIqkAAnERaxtY9NlI9G9vFufE93IBAAMCAAN5AAM6BA",
    "logic_gate": "AgACAgIAAyEFAATh7MR7AANyaZpexwtg_I0s5iQ8b6vhncHdQ5IAAnIRaxtY9NlIqutJSYkMKYABAAMCAAN5AAM6BA",
    "compass": "AgACAgIAAyEFAATh7MR7AANzaZpeyrrg3o5TYE2qIRKAmlXOHOYAAnMRaxtY9NlIR-LNwGDT1sABAAMCAAN5AAM6BA",
    "master_key": "AgACAgIAAyEFAATh7MR7AAN0aZpeyws4ZgQhHZM5wVTOYTWyX1oAAnQRaxtY9NlIfbzkA2fqqcABAAMCAAN5AAM6BA",
    "abyssal_key": "AgACAgIAAyEFAATh7MR7AAOWaZtdX00_n9qBT9R4r5b5Fe_68FsAArITaxtY9OFIKDNn2xcLjq0BAAMCAAN5AAM6BA", # Updated
    "battery": "AgACAgIAAyEFAATh7MR7AAN2aZpezuDtMGabjCNUebCWvjz9uQcAAnYRaxtY9NlIXTtrQzBAbTsBAAMCAAN5AAM6BA",
    "neural_stimulator": "AgACAgIAAyEFAATh7MR7AAN3aZpe0DukjqYY04WI0mEvJjXAnvYAAncRaxtY9NlIpAHQqiPYRnoBAAMCAAN5AAM6BA",
    "firewall": "AgACAgIAAyEFAATh7MR7AAN4aZpe0b0Nqd4a2I8Z3g8DTeb3ltEAAngRaxtY9NlIYzpKZGqtcGkBAAMCAAN5AAM6BA",
    "ice_trap": "AgACAgIAAyEFAATh7MR7AAN5aZpe00k5e0TXJatZvkf28dBVnPEAAnkRaxtY9NlI_mmEBqcmZ6EBAAMCAAN5AAM6BA",
    "proxy_server": "AgACAgIAAyEFAATh7MR7AAN6aZpe1dY0TbutdZ-ChGnJjK0BPyEAAnoRaxtY9NlIYaWgsP2NXKcBAAMCAAN5AAM6BA",
    "emp_grenade": "AgACAgIAAyEFAATh7MR7AAN7aZpe1okpfUFkYnIG0hzfCrdNg_8AAnsRaxtY9NlIxqTEHZzQ8BEBAAMCAAN5AAM6BA",
    "stealth_spray": "AgACAgIAAyEFAATh7MR7AAN8aZpe2Mtno-JWlzcWwI4YSkfuR_MAAnwRaxtY9NlIIIsgHoSfgJIBAAMCAAN5AAM6BA",
    "data_spike": "AgACAgIAAyEFAATh7MR7AAN9aZpe2k-3Usl-W6nVyfef750feiAAAn0RaxtY9NlIAQNtcLV_9LkBAAMCAAN5AAM6BA",
    "memory_wiper": "AgACAgIAAyEFAATh7MR7AAN-aZpe204r9jvb9cxOVsSilMs3bt8AAn4RaxtY9NlIwKa7VvZ_LgwBAAMCAAN5AAM6BA",
    "aegis": "AgACAgIAAyEFAATh7MR7AAN_aZpe3KpKqLpMXKwuQq1fd8lorS0AAn8RaxtY9NlI5f8UvLYErEkBAAMCAAN5AAM6BA",
    "admin_key": "AgACAgIAAyEFAATh7MR7AAOAaZpe3q6IgMM3ivy5EZPUhTgu8agAAoARaxtY9NlI1ulNFuu5f0wBAAMCAAN5AAM6BA",
    "cryo": "AgACAgIAAyEFAATh7MR7AAOBaZpe4FnaJqitOKn8AWH9kR3WU1cAAoERaxtY9NlIYC9aaZHpLcIBAAMCAAN5AAM6BA",
    "accel": "AgACAgIAAyEFAATh7MR7AAOCaZpe4XV0Zv0pbI5Rv22eo2xOujcAAoIRaxtY9NlI5oUbxwUBN74BAAMCAAN5AAM6BA",
    "decoder": "AgACAgIAAyEFAATh7MR7AAODaZpe47Cr5Sv7Jw6jZDdVp_kl-i8AAoMRaxtY9NlIrOEz55TIHPYBAAMCAAN5AAM6BA",
    "purification_sync": "AgACAgIAAyEFAATh7MR7AAOEaZpe5GSXiXv69zoIy_1Lc8BXGIQAAoQRaxtY9NlIAnYHi_sKi4wBAAMCAAN5AAM6BA",
    "encrypted_cache": "AgACAgIAAyEFAATh7MR7AAOFaZpe5o-sK_0a0m8VH-R8C1Oq1vsAAoURaxtY9NlIy6S2f5OWBZIBAAMCAAN5AAM6BA",
    "fragment": "AgACAgIAAyEFAATh7MR7AAOGaZpe6Ejkvq2Ja3UrVd2hKdEcbnMAAoYRaxtY9NlIaswytRpljt4BAAMCAAN5AAM6BA",
    "tactical_scanner": "AgACAgIAAyEFAATh7MR7AAODaZpe47Cr5Sv7Jw6jZDdVp_kl-i8AAoMRaxtY9NlIrOEz55TIHPYBAAMCAAN5AAM6BA",
    # [NEW] Cursed Chest Drops (Ultra Rare)
    "credit_slicer": "AgACAgIAAyEFAATh7MR7AAOraZ1y3Mhuw9lZmEO3ar1v4t2bY-4AAsoUaxuNZulIthKaalQ-VfYBAAMCAAN5AAM6BA",
    "banhammer_shard": "AgACAgIAAyEFAATh7MR7AAOqaZ1y3MJ5WOvTGDITbzdP4PvUj_EAAskUaxuNZulIySuBj3mJttEBAAMCAAN5AAM6BA",
    "grandfather_paradox": "AgACAgIAAyEFAATh7MR7AAOpaZ1y3KxsUTjor7oe7J-krEWW39wAAsgUaxuNZulIkGWgeui1zsQBAAMCAAN5AAM6BA",
    "empath_whip": "AgACAgIAAyEFAATh7MR7AAOoaZ1y3DAyrOhW2f7jQuAPByIdulYAAscUaxuNZulII0o01VJ2SZQBAAMCAAN5AAM6BA",
    "cache_wiper": "AgACAgIAAyEFAATh7MR7AAOnaZ1y3JjGO3PxddF53zkYQFrW9uEAAsYUaxuNZulIfZ97LcIVA-kBAAMCAAN5AAM6BA",
    "error_404_mirror": "AgACAgIAAyEFAATh7MR7AAOmaZ1y3GdkSlaOp_znEhXa6ntVKQYAAsUUaxuNZulIOq7D4ufepsoBAAMCAAN5AAM6BA",
    "judas_shell": "AgACAgIAAyEFAATh7MR7AAOlaZ1y3DikmjIGqcTctX56ZY45xesAAsQUaxuNZulI1DlqZfy1JMsBAAMCAAN5AAM6BA",
    "holo_poverty": "AgACAgIAAyEFAATh7MR7AAOkaZ1y3FinUH8FR_8_LShkAfme7-8AAsMUaxuNZulI9Qm_4JmStWgBAAMCAAN5AAM6BA",
    "schrodinger_armor": "AgACAgIAAyEFAATh7MR7AAOjaZ1y3Mjca8ooZBTkqo3tk7cfpZMAAsIUaxuNZulIUfnpegmjg70BAAMCAAN5AAM6BA",
    "thermonuclear_shroud": "AgACAgIAAyEFAATh7MR7AAOiaZ1y3JJt1fR52SbyAn0-HC1BA4AAAsEUaxuNZulIZRh6GV_ZCRoBAAMCAAN5AAM6BA",
    "blood_miner": "AgACAgIAAyEFAATh7MR7AAOhaZ1y2gZtZZVuinzp3BUIIVpgrx0AAsAUaxuNZulIoizBLV9Dx64BAAMCAAN5AAM6BA",
    "karma_inversion": "AgACAgIAAyEFAATh7MR7AAOgaZ1y2vWSGvx9sktHm0h_kP6vZo0AAr8UaxuNZulI0fhDCtbcRowBAAMCAAN5AAM6BA",
    "oblivion_chip": "AgACAgIAAyEFAATh7MR7AAOfaZ1y2jngEPtU6b3vXXYhOac6-7AAAr4UaxuNZulI8rWKNaGLspgBAAMCAAN5AAM6BA",
    "imposter_syndrome": "AgACAgIAAyEFAATh7MR7AAOeaZ1y2uTGVC97oWcesLl9js_J91sAAr0UaxuNZulIKCTZl-vBWHQBAAMCAAN5AAM6BA",
    "kamikaze_protocol": "AgACAgIAAyEFAATh7MR7AAOdaZ1y2sIo3BByfvPiWuBkCogJoR0AArwUaxuNZulIUcv3MZlrjogBAAMCAAN5AAM6BA",
    "architect_eye": "AgACAgIAAyEFAATh7MR7AAOcaZ1y2vnepclZE8UXC8w2BwPy808AArsUaxuNZulI52GkGPQKQ4cBAAMCAAN5AAM6BA",
    "crown_paranoia": "AgACAgIAAyEFAATh7MR7AAObaZ1y2kwZ3UK-fFGKU75qD7fTOXEAAroUaxuNZulIJomyCKT66asBAAMCAAN5AAM6BA",
    "death_mask": "AgACAgIAAyEFAATh7MR7AAOaaZ1y2mvA-SvPzdi0Nt4MDqWNG_AAArkUaxuNZulIAQMwqqnCzTYBAAMCAAN5AAM6BA",
    "reality_silencer": "AgACAgIAAyEFAATh7MR7AAOZaZ1y2r0rJdkxwk57DgABWHfL3hAlAAK4FGsbjWbpSNK-mgnqWJ7uAQADAgADeQADOgQ",
    "martyr_halo": "AgACAgIAAyEFAATh7MR7AAOYaZ1y2pH5oTr8BLKXGGkS6g2re3AAArcUaxuNZulIWO-j5VXKuLQBAAMCAAN5AAM6BA"
}

# =============================================================================
# PVP & CYBERDECK CONFIG (v2.0)
# =============================================================================

# Файл ID для картинок ПО
SOFTWARE_IMAGES = {
    "soft_brute_v1": "AgACAgIAAyEFAATh7MR7AAPIaZ2VLVjGqy3sSPQS1ds61F9CccEAAoQWaxuNZulI3vrAQHqxAi8BAAMCAAN5AAM6BA",
    "soft_trojan_v1": "AgACAgIAAyEFAATh7MR7AAPHaZ2VLJSYHGmrWd_K9MglJi0w780AAoMWaxuNZulIimsgUVs_AkcBAAMCAAN5AAM6BA",
    "soft_ddos_v1": "AgACAgIAAyEFAATh7MR7AAPGaZ2VK1n9Lxxi4aGpfYnJKItE6cwAAoIWaxuNZulImww_FQN8hfUBAAMCAAN5AAM6BA",
    "soft_wall_v1": "AgACAgIAAyEFAATh7MR7AAPFaZ2VKQRX-7Ovm1zdt7PWCk97XHMAAoAWaxuNZulIsOsUuXJPoMQBAAMCAAN5AAM6BA",
    "soft_ice_v1": "AgACAgIAAyEFAATh7MR7AAPEaZ2VKNv27yHXg7ozJPypOh-eT9EAAn8WaxuNZulIIgXFPTmQYQYBAAMCAAN5AAM6BA",
    "soft_aegis_v1": "AgACAgIAAyEFAATh7MR7AAPDaZ2VJh-QOJ_v1UloWsnrYk9nq8AAAn4WaxuNZulIpciY9YD-JY4BAAMCAAN5AAM6BA",
    "soft_vpn_v1": "AgACAgIAAyEFAATh7MR7AAPCaZ2VJXeTIlwuzFMU02B0oBCWmqkAAn0WaxuNZulIwDEme3FKMwMBAAMCAAN5AAM6BA",
    "soft_sniffer_v1": "AgACAgIAAyEFAATh7MR7AAPBaZ2VJF1PWEcoHfKwG-IFQXpdR10AAnwWaxuNZulIpyHTZv-OjYcBAAMCAAN5AAM6BA",
    "soft_backdoor_v1": "AgACAgIAAyEFAATh7MR7AAPAaZ2VI4vEBkuYzT5ldiv0Lql3jK4AAnsWaxuNZulIG0pVUPJ5RtQBAAMCAAN5AAM6BA"
}

ITEM_IMAGES.update(SOFTWARE_IMAGES)

SOFTWARE_DB = {
    # 🔴 ATK (Attack / BruteForce)
    "soft_brute_v1": {
        "name": "🔴 БрутФорс.exe", "type": "atk", "power": 1, "cost": 100, "durability": 10,
        "desc": "Базовая атака. Ломает Стены.\n[ЛОР]: Простая, но эффективная утилита перебора паролей. Громкая и грязная, как удар кувалдой по серверной стойке.",
        "icon": "🔴"
    },
    "soft_trojan_v1": {
        "name": "🔴 Троян.bat", "type": "atk", "power": 2, "cost": 250, "durability": 1,
        "desc": "Атака с шансом крита (х2 награда). Одноразовая.\n[ЛОР]: Маскируется под системное обновление. Когда жертва понимает ошибку, ее кошелек уже пуст.",
        "icon": "🔴"
    },
    "soft_ddos_v1": {
        "name": "🔴 DDoS-Пушка", "type": "atk", "power": 3, "cost": 500, "durability": 1,
        "desc": "Мощная атака. Пробивает даже продвинутые щиты. Одноразовая.\n[ЛОР]: Ионная пушка цифрового мира. Заваливает канал жертвы мусорным трафиком до полного отказа систем жизнеобеспечения.",
        "icon": "🔴"
    },

    # 🔵 DEF (Defense / Firewall)
    "soft_wall_v1": {
        "name": "🔵 Файрвол 1.0", "type": "def", "power": 1, "cost": 100, "durability": 10,
        "desc": "Базовая защита. Блокирует Стелс.\n[ЛОР]: Стандартный пакет фильтрации трафика. Отсекает скрипт-кидди и любопытных ботов.",
        "icon": "🔵"
    },
    "soft_ice_v1": {
        "name": "🔵 Ледяная Стена", "type": "def", "power": 2, "cost": 250, "durability": 1,
        "desc": "Защита + наносит урон атакующему при успехе. Одноразовая.\n[ЛОР]: 'Intrusion Countermeasures Electronics'. Черный лед, который не просто останавливает взломщика, а выжигает его нейронные связи.",
        "icon": "🔵"
    },
    "soft_aegis_v1": {
        "name": "🔵 Ядро Эгиды", "type": "def", "power": 3, "cost": 500, "durability": 5,
        "desc": "Абсолютная защита. Отражает 80% атак.\n[ЛОР]: Автономный защитный модуль военного образца. Создает вокруг данных непроницаемый купол шифрования.",
        "icon": "🔵"
    },

    # 🟢 STL (Stealth / Utility)
    "soft_vpn_v1": {
        "name": "🟢 VPN-Призрак", "type": "stl", "power": 1, "cost": 100, "durability": 10,
        "desc": "Базовый стелс. Обходит Ловушки (Атаку).\n[ЛОР]: Перенаправляет твой сигнал через сотни мертвых узлов. Ты становишься призраком в машине.",
        "icon": "🟢"
    },
    "soft_sniffer_v1": {
        "name": "🟢 Сниффер", "type": "stl", "power": 1, "cost": 200, "durability": 5,
        "desc": "Показывает 1 слот врага перед боем.\n[ЛОР]: Пассивный анализатор пакетов. Позволяет увидеть, какие козыри спрятаны в рукаве у противника.",
        "icon": "🟢"
    },
    "soft_backdoor_v1": {
        "name": "🟢 Бэкдор.js", "type": "stl", "power": 3, "cost": 500, "durability": 1,
        "desc": "Продвинутый стелс. Крадет данные даже при ничьей. Одноразовая.\n[ЛОР]: Заранее внедренный эксплойт. Ты заходишь не через парадную дверь, а через служебный вход, оставленный ленивым админом.",
        "icon": "🟢"
    }
}

PVP_HARDWARE = ['firewall', 'ice_trap', 'proxy_server', 'hw_firewall', 'hw_ice_trap', 'hw_proxy_server']
PVP_ITEMS = set(SOFTWARE_DB.keys()) | set(PVP_HARDWARE)

DECK_UPGRADES = {
    1: {"slots": 1, "cost": 0},
    2: {"slots": 2, "cost": 500},
    3: {"slots": 3, "cost": 1500}
}

PVP_CONSTANTS = {
    "SHIELD_DURATION": 14400,  # 4 hours
    "PROTECTION_LIMIT": 500,   # Min BioCoins to be attacked
    "HACK_REWARD": 25,         # Base BioCoin reward (Mining)
    "STEAL_PERCENT": 0.10,     # 10% of coins
    "MAX_STEAL": 15            # Max %
}

RAID_EVENT_IMAGES = {
    "riddle": "AgACAgIAAyEFAATh7MR7AAOMaZplE9yRGp0OQ7wrI08MXvVstDIAApQRaxtY9NlIuWaeLR2EvfcBAAMCAAN5AAM6BA",
    "remains": "AgACAgIAAyEFAATh7MR7AAOLaZplEvzNEMCrtEsHBPXeNOJWPQYAApMRaxtY9NlIerWDJ64TzH8BAAMCAAN5AAM6BA",
    "anomaly": "AgACAgIAAyEFAATh7MR7AAOQaZpyhK1AY9GJvFUOes8zON5xTdkAAqkRaxtY9NlIHukCW_0hITcBAAMCAAN5AAM6BA",
    "trap": "AgACAgIAAyEFAATh7MR7AAOJaZplDMtrnHjusNp5OsUs3yL91Z0AApERaxtY9NlIK-ZbCj50RtQBAAMCAAN5AAM6BA",
    "chest": "AgACAgIAAxkBAAIJ0mmaZYMBFJvBddCi_pRyj2aPC7joAAJpFmsbeDnQSGpWGk1JE0a5AQADAgADeQADOgQ",
    "chest_opened": "AgACAgIAAyEFAATh7MR7AAOUaZpyhdBJsOgbJKKviXWKiBO9NyMAAq0RaxtY9NlID8lyj0zhiVYBAAMCAAN5AAM6BA",
    "loot": "AgACAgIAAyEFAATh7MR7AAORaZpyhP_DD5_UGMt9_v8iu8bmMSAAAqoRaxtY9NlITLsj7TgPlWABAAMCAAN5AAM6BA",
    "safe_zone": "AgACAgIAAyEFAATh7MR7AAOHaZpk-8Gm-LfUWWaZfQlUwHLyRQUAAo8RaxtY9NlIzkh5EGccQjQBAAMCAAN5AAM6BA",
    "death": "AgACAgIAAyEFAATh7MR7AAOSaZpyhA87aQRq1boXbpGvwPu2uQgAAqsRaxtY9NlIhptJZqm7ccYBAAMCAAN5AAM6BA",
    "glitch": "AgACAgIAAyEFAATh7MR7AAOPaZpmfiE9oMG9bAHzOeS_LRjBfb4AApgRaxtY9NlIW1IUbTg7iwEBAAMCAAN5AAM6BA",
    "evacuation": "AgACAgIAAyEFAATh7MR7AAOTaZpyhOJGNziiFA14uFgz0EZFwc4AAqwRaxtY9NlI5ClQPS_n0BQBAAMCAAN5AAM6BA",
    "cursed_chest": "AgACAgIAAyEFAATh7MR7AAOVaZtdX-DlcF23Xe38TUTV9T3SwucAArETaxtY9OFItm6V9NRCnugBAAMCAAN5AAM6BA",
    "cursed_chest_opened": "AgACAgIAAyEFAATh7MR7AAOXaZtdX-HmNHBDJve48wwy6h0te2gAArMTaxtY9OFIchMB7mz9pmMBAAMCAAN5AAM6BA"
}

# =============================================================================
# 2. НЕЙРО-ЭКОНОМИКА (ARPG БАЛАНС)
# =============================================================================
COOLDOWN_BASE = 1800      
COOLDOWN_ACCEL = 900      
COOLDOWN_SIGNAL = 300     

XP_GAIN = 25              
XP_SIGNAL = 15            
RAID_COST = 100           
RAID_STEP_COST = 15       
PATH_CHANGE_COST = 100    
REFERRAL_BONUS = 300
ARCHIVE_COST = 500

# [NEW] Cost Scaling: 1st=100, 2nd=200, 3rd+=400
RAID_ENTRY_COSTS = [100, 200, 400]

# PVP CONSTANTS
PVP_FIND_COST = 50
PVP_DIRTY_COST = 50
PVP_STEALTH_COST = 150
PVP_RESET_COST = 20
PVP_REVENGE_PENALTY = 0.10
PVP_COOLDOWN = 7200 # 2 hours
QUARANTINE_LEVEL = 3

INVENTORY_LIMIT = 20

# --- РЫНОЧНЫЕ КОТИРОВКИ (BioCoins) ---
PRICES = {
    # Апгрейды
    "cryo": 200,          
    "accel": 600,         
    "decoder": 1000,
    # Расходники
    "compass": 150,
    "tactical_scanner": 300,
    "master_key": 75,    
    "battery": 250,
    "aegis": 400,
    "fragment": 5000,
    # [NEW]
    "abyssal_key": 500,
    "neural_stimulator": 300,
    "firewall": 1000,
    "ice_trap": 2000,
    "proxy_server": 500, # XP PRICE
    "emp_grenade": 200,
    "stealth_spray": 350,
    "data_spike": 120,
    "memory_wiper": 400,
    "nomad_goggles": 500,
    "scavenger_mask": 800,
    "tactical_helmet": 2500,
    "vampire_visor": 4000,
    "cyber_halo": 8000,
    "overclock_crown": 9500,
    "void_walker_hood": 18000,
    "architect_mask": 25000,
    "relic_vampire": 50000,
    "relic_speed": 75000,
    "purification_sync": 50000
}

# =============================================================================
# 3. ЭКИПИРОВКА И ПРЕДМЕТЫ
# =============================================================================
SLOTS = {'head': '🧢 ГОЛОВА', 'body': '👕 ТЕЛО', 'weapon': '⚔️ ОРУЖИЕ', 'chip': '💾 ЧИП', 'eidos_shard': '👁 МЕНТАЛЬНОЕ ЯДРО'}

# База Экипировки (Расширенный Лор + Уникальные Иконки) v26.3
EQUIPMENT_DB = {
    # ==========================
    # АБСОЛЮТ (VIP)
    # ==========================
    "eidos_shard": {
        "name": "👁 СИНХРОНИЗАТОР АБСОЛЮТА",
        "slot": "eidos_shard", "atk": 0, "def": 0, "luck": 0, "price": 0,
        "desc": "[ЭЙДОС]: Дает особый статус никнейма. Создан из чистого опыта.Потерянная форма обретает истинную ценность лишь в отражении чужого преодоления."
    },
    # ==========================
    # ОРУЖИЕ (WEAPONS)
    # ==========================
    "rusty_knife": {
        "name": "⚪️ 🔪 РЖАВЫЙ ТЕСАК",
        "slot": "weapon", "atk": 5, "def": 0, "luck": 0, "price": 50,
        "desc": "[МЕХАНИКА]: +5 ATK. Базовый урон. Повышает шансы выжить на первых этажах Пустоши.\n[ЛОР]: Кусок заточенного цифрового лома, обильно покрытый коррозией битых пикселей. Осколки, только что очнувшиеся от спячки Системы, находят такие в горах удаленного мусора. На шероховатой рукояти выцарапано чье-то стертое ID. Оружие не столько режет, сколько вносит ошибки в код противника, вызывая микро-сбои."
    },
    "crowbar": {
        "name": "⚪️ 🔧 МОНТИРОВКА ХАКЕРА",
        "slot": "weapon", "atk": 10, "def": 0, "luck": 1, "price": 150,
        "desc": "[МЕХАНИКА]: +10 ATK. Надежное средство для взлома черепов и старых терминалов.\n[ЛОР]: Увесистый кусок арматуры из эпохи раннего интернета. Говорят, именно этим инструментом пользовался первый Архитектор, когда серверы впервые дали сбой, чтобы вручную перезапустить охлаждение. Металл всегда холодный на ощупь и почему-то пахнет озоном и старым пластиком."
    },
    "data_bat": {
        "name": "⚪️ 🏏 БИТА-НОСИТЕЛЬ",
        "slot": "weapon", "atk": 15, "def": 0, "luck": 2, "price": 300,
        "desc": "[МЕХАНИКА]: +15 ATK. Тяжелое дробящее оружие. Имеет небольшой шанс удачи при луте.\n[ЛОР]: Уличные скрипт-кидди Даркнета модифицировали обычные бейсбольные биты, вшивая в них тяжелые свинцовые модули памяти. При ударе эта бита не просто ломает физическую оболочку, но и принудительно загружает в голову жертвы терабайты информационного мусора. Жертва погибает от перегрузки сознания."
    },
    "shock_baton": {
        "name": "🔵 🦯 ШОКОВАЯ ДУБИНКА",
        "slot": "weapon", "atk": 25, "def": 0, "luck": 0, "price": 800,
        "desc": "[МЕХАНИКА]: +25 ATK. Отличное средство контроля толпы. Идеально против Дронов-Стражей.\n[ЛОР]: Стандартное табельное оружие Полиции Мыслей. Внутри рукояти спрятан конденсатор, способный выдать разряд, стирающий краткосрочную память. Снята с мертвого патрульного на окраине Корпоративных Архивов. На корпусе мигает красная надпись: «Несанкционированный пользователь. Гарантия аннулирована»."
    },
    "cyber_katana": {
        "name": "🔵 🗡 КИБЕР-КАТАНА",
        "slot": "weapon", "atk": 35, "def": 2, "luck": 5, "price": 1200,
        "desc": "[МЕХАНИКА]: +35 ATK / +2 DEF. Сбалансированное лезвие, позволяющее парировать легкие атаки.\n[ЛОР]: Элегантное оружие забытой эпохи нео-самураев. Мономолекулярное лезвие настолько тонкое, что способно разрезать поток данных между серверами. Клинок тихо гудит в тишине и оставляет за собой неоновый след в воздухе. Выбор тех, кто предпочитает эстетику в искусстве убийства."
    },
    "laser_pistol": {
        "name": "🔵 🔫 ЛАЗЕРНЫЙ ИЗЛУЧАТЕЛЬ",
        "slot": "weapon", "atk": 45, "def": 0, "luck": 3, "price": 2000,
        "desc": "[МЕХАНИКА]: +45 ATK. Огнестрельное оружие среднего радиуса. Прожигает начальную броню.\n[ЛОР]: Компактный, легкий, смертоносный. Вместо пуль использует сфокусированные пучки фотонов, зашифрованные смертельным кодом. На потертой рукояти криво выгравировано: «Свет — это тоже информация, просто очень быстрая и не оставляющая шансов на ответ». Перегревается после десятого выстрела."
    },
    "plasma_rifle": {
        "name": "🟣 🔭 ПЛАЗМЕННЫЙ РЕЛЬСОТРОН",
        "slot": "weapon", "atk": 65, "def": 5, "luck": 10, "price": 5000,
        "desc": "[МЕХАНИКА]: +65 ATK / +5 DEF. Тяжелая артиллерия. Плазма дает шанс на критические повреждения.\n[ЛОР]: Запрещенная разработка радикальной фракции Техно. Система объявила это оружие вне закона, так как нестабильная плазма прожигает дыры не только во врагах, но и в самой ткани виртуальной реальности. Выстрел из рельсотрона звучит как разрыв барабанной перепонки и оставляет в воздухе запах горелого вакуума."
    },
    "nano_blade": {
        "name": "🟣 🧬 НАНО-КЛИНОК",
        "slot": "weapon", "atk": 80, "def": 0, "luck": 15, "price": 7500,
        "desc": "[МЕХАНИКА]: +80 ATK. Игнорирует базовые щиты мобов. Смертоносная точность.\n[ЛОР]: Это не просто меч, это колония из миллиарда хищных нано-машин, объединенных в форму клинка. Они постоянно перестраивают режущую кромку, делая её идеальной для конкретного материала брони противника. Если долго смотреть на лезвие, можно увидеть, как оно шевелится, словно живое."
    },
    "void_cannon": {
        "name": "🟠 🌌 ПУШКА ПУСТОТЫ",
        "slot": "weapon", "atk": 120, "def": 10, "luck": 0, "price": 15000,
        "desc": "[МЕХАНИКА]: +120 ATK. Легендарный артефакт. Аннигилирует боссов высоких уровней за считанные ходы.\n[ЛОР]: Венец творения Архитекторов. Она не наносит урон в привычном понимании. Она создает локальную точку Абсолютного Ничто, которая засасывает и стирает фрагменты кода противника. Оружие, созданное для удаления бракованных вселенных, теперь в твоих руках. Каждое использование отнимает у тебя крупицу воспоминаний."
    },
    "singularity_sword": {
        "name": "🟠 🌠 МЕЧ СИНГУЛЯРНОСТИ",
        "slot": "weapon", "atk": 100, "def": 25, "luck": 20, "price": 20000,
        "desc": "[МЕХАНИКА]: +100 ATK / +25 DEF. Идеальный баланс атаки и защиты. Искажает пространство.\n[ЛОР]: Выкован в самом эпицентре Ядра Тьмы из кристаллизованного времени. Тот, кто держит его в руках, выпадает из привычного течения секунд. Пока враг только замахивается, ты уже наносишь три удара. Лезвие не отражает свет — оно его поглощает, оставляя в пространстве черную кровоточащую рану."
    },

    # ==========================
    # ГОЛОВНЫЕ УБОРЫ И АУРЫ (HEAD)
    # ==========================
    "nomad_goggles": {
        "name": "⚪️ 🥽 ОКУЛЯРЫ КОЧЕВНИКА",
        "slot": "head", "atk": 0, "def": 2, "luck": 5, "price": 500,
        "desc": "[АУРА: ИСКАТЕЛЬ]: +5% шанс найти лут в пустой комнате.\n[ЛОР]: Простые антибликовые очки с наложенным фильтром дополненной реальности. Позволяют разглядеть забытые монеты среди битых пикселей."
    },
    "scavenger_mask": {
        "name": "⚪️ 😷 РЕСПИРАТОР СТАЛКЕРА",
        "slot": "head", "atk": 2, "def": 5, "luck": 0, "price": 800,
        "desc": "[АУРА: ФИЛЬТРАЦИЯ]: Снижает урон от всех Ловушек на фиксированные 5 ед.\n[ЛОР]: Фильтрует не только токсичный воздух старых серверов, но и вредоносный код базовых вирусов."
    },
    "tactical_helmet": {
        "name": "🔵 🪖 ШЛЕМ ТАКТИЧЕСКОГО ОТЛИКА",
        "slot": "head", "atk": 5, "def": 10, "luck": 0, "price": 2500,
        "desc": "[АУРА: ПРЕДВИДЕНИЕ]: Дает 10% шанс автоматически уклониться от атаки врага (Побег без нажатия кнопки).\n[ЛОР]: Встроенный сопроцессор считывает микро-изменения в коде врага за миллисекунду до удара."
    },
    "vampire_visor": {
        "name": "🔵 🩸 НЕЙРО-ВИЗОР «ПИЯВКА»",
        "slot": "head", "atk": 10, "def": 0, "luck": 0, "price": 4000,
        "desc": "[АУРА: ВАМПИРИЗМ I]: При убийстве врага восстанавливает 5% Сигнала.\n[ЛОР]: Запрещенный имплант синдиката Крови. Перегоняет остаточный код убитой программы прямо в систему жизнеобеспечения носителя."
    },
    "cyber_halo": {
        "name": "🟣 🪩 ГОЛОГРАФИЧЕСКИЙ НИМБ",
        "slot": "head", "atk": 0, "def": 15, "luck": 20, "price": 8000,
        "desc": "[АУРА: СВЯТОЙ КОД]: 20% шанс, что смертельный удар оставит вам 1% Сигнала вместо смерти (кулдаун 1 раз за бой).\n[ЛОР]: Светящийся круг над головой. Программа защиты, написанная религиозным культом ИИ."
    },
    "overclock_crown": {
        "name": "🟣 👑 ВЕНЕЦ РАЗГОНА",
        "slot": "head", "atk": 25, "def": -10, "luck": 0, "price": 9500,
        "desc": "[АУРА: ПЕРЕГРУЗКА]: Удваивает шанс КРИТА, но каждый ваш КРИТ отнимает 2% Сигнала у вас.\n[ЛОР]: Терновый венец из оголенных проводов. Заставляет процессор работать на 300% мощности, сжигая нейроны."
    },
    "void_walker_hood": {
        "name": "🟠 🌌 КАПЮШОН ПУСТОТНОГО ШАГА",
        "slot": "head", "atk": 10, "def": 10, "luck": 15, "price": 18000,
        "desc": "[АУРА: ДВОЙНОЙ ШАГ]: 25% шанс пройти 2 метра глубины за один клик (экономия энергии).\n[ЛОР]: Ткань соткана из темной материи. Носящий её существует сразу в двух точках пространства одновременно."
    },
    "architect_mask": {
        "name": "🟠 🎭 ЛИЦО АРХИТЕКТОРА",
        "slot": "head", "atk": 20, "def": 20, "luck": 0, "price": 25000,
        "desc": "[АУРА: ЗЕРКАЛО]: Возвращает 30% полученного урона обратно в атакующего моба.\n[ЛОР]: Гладкая безликая маска из жидкого хрома. В ней враг видит лишь собственный неотвратимый конец."
    },
    "relic_vampire": {
        "name": "🔴 🦇 КОРОНА ИСТИННОЙ КРОВИ (Реликвия)",
        "slot": "head", "atk": 30, "def": 10, "luck": 10, "price": 50000,
        "desc": "[АУРА: ИСТИННЫЙ ВАМПИРИЗМ]: Лечит 2% Сигнала при КАЖДОМ успешном ударе по врагу (не только при убийстве).\n[ЛОР]: Артефакт из эпохи Первой Войны Серверов. Делает вас практически бессмертным, пока вы наносите урон."
    },
    "relic_speed": {
        "name": "🔴 ⚡️ ШЛЕМ БОГА СКОРОСТИ (Реликвия)",
        "slot": "head", "atk": 15, "def": 15, "luck": 30, "price": 75000,
        "desc": "[АУРА: ГИПЕРПРОСТРАНСТВО]: Каждый шаг в Рейде ВСЕГДА равен 2 метрам. XP тратится как за 1.\n[ЛОР]: Древний модуль. В нём время замирает. Для Системы вы телепортируетесь. Тот самый шмот, ради которого стоит копить монеты."
    },
    "shadow_reliq-speed": {
        "name": "🔴 ⚡️ ШЛЕМ БОГА СКОРОСТИ (Реликвия)",
        "slot": "head", "atk": 15, "def": 15, "luck": 30, "price": 75000,
        "desc": "[АУРА: ГИПЕРПРОСТРАНСТВО]: Каждый шаг в Рейде ВСЕГДА равен 2 метрам. XP тратится как за 1.\n[ЛОР]: Древний модуль. В нём время замирает. Для Системы вы телепортируетесь. Тот самый шмот, ради которого стоит копить монеты."
    },
    "Tac_visor": {
        "name": "🔵 🪖 ШЛЕМ ТАКТИЧЕСКОГО ОТЛИКА",
        "slot": "head", "atk": 5, "def": 10, "luck": 0, "price": 2500,
        "desc": "[АУРА: ПРЕДВИДЕНИЕ]: Дает 10% шанс автоматически уклониться от атаки врага (Побег без нажатия кнопки).\n[ЛОР]: Встроенный сопроцессор считывает микро-изменения в коде врага за миллисекунду до удара."
    },

    # ==========================
    # БРОНЯ (ARMOR)
    # ==========================
    "hoodie": {
        "name": "⚪️ 🥼 БАЛАХОН СКВИТТЕРА",
        "slot": "armor", "atk": 0, "def": 5, "luck": 1, "price": 50,
        "desc": "[МЕХАНИКА]: +5 DEF. Простейшая защита от непогоды Нулевого Слоя и мелких паразитов.\n[ЛОР]: Выцветший, мешковатый балахон. Базовая одежда тех, кто предпочитает скрывать свое лицо и интерфейс в тени капюшона. Ткань прошита медными нитями, которые немного искажают сигналы поисковых сканеров Системы. Не спасет от пули, но поможет затеряться в толпе ботов."
    },
    "leather_jacket": {
        "name": "⚪️ 🧥 КУРТКА СИНДИКАТА",
        "slot": "armor", "atk": 0, "def": 10, "luck": 0, "price": 150,
        "desc": "[МЕХАНИКА]: +10 DEF. Плотный материал глушит слабые удары и укусы глитч-тварей.\n[ЛОР]: Тяжелая, скрипучая искусственная кожа, насквозь пропитанная запахом машинного масла и дешевых неоновых трубок. Негласный символ бунтарей и контрабандистов Даркнета. На спине тускло светится стертая эмблема забытой группировки. Носить её — значит показать Системе средний палец."
    },
    "kevlar_vest": {
        "name": "🔵 🦺 БРОНЕЖИЛЕТ ОХРАНЫ",
        "slot": "armor", "atk": 0, "def": 15, "luck": 0, "price": 300,
        "desc": "[МЕХАНИКА]: +15 DEF. Отлично держит кинетический урон и останавливает пули среднего калибра.\n[ЛОР]: Армейский кевлар, усиленный керамическими пластинами. Оставлен корпоративными войсками во времена Великой Перезагрузки, когда солдаты массово теряли рассудок. На груди видны следы от когтей Стирателя — предыдущему владельцу эта броня не сильно помогла, но, возможно, тебе повезет больше."
    },
    "tactical_suit": {
        "name": "🔵 🥋 ТАКТИЧЕСКИЙ КОМБИНЕЗОН",
        "slot": "armor", "atk": 5, "def": 22, "luck": 2, "price": 1000,
        "desc": "[МЕХАНИКА]: +22 DEF / +5 ATK. Не сковывает движения, содержит модули для скрытого ношения оружия.\n[ЛОР]: Умная ткань, которая подстраивается под температуру тела и окружающей среды. Костюм буквально напичкан скрытыми карманами для стимуляторов и батарей. Встроенная система охлаждения позволяет не потерять сознание, когда адреналин и Сигнал бьют ключом в разгаре жестокого рейда."
    },
    "exo_skeleton": {
        "name": "🟣 🦾 ГОРНОПРОХОДЧЕСКИЙ ЭКЗОСКЕЛЕТ",
        "slot": "armor", "atk": 20, "def": 30, "luck": 0, "price": 3500,
        "desc": "[МЕХАНИКА]: +30 DEF / +20 ATK. Превращает носителя в ходячий танк. Сильный бонус к атаке тяжелым оружием.\n[ЛОР]: Грубый, неповоротливый, но невероятно мощный промышленный каркас. Раньше использовался шахтерами при глубинной добыче крипты на нижних уровнях серверов. Гидравлические поршни с шипением усиливают каждое твое движение, позволяя ломать кости врагам голыми руками. Минус — ты шумишь, как товарный поезд."
    },
    "nano_suit": {
        "name": "🟣 🦠 СИМБИОТИЧЕСКИЙ НАНО-КОСТЮМ",
        "slot": "armor", "atk": 10, "def": 40, "luck": 5, "price": 2000,
        "desc": "[МЕХАНИКА]: +40 DEF / +10 ATK. Идеальная защита. Амортизирует до 80% входящего физического урона.\n[ЛОР]: Это не одежда, это миллионы разумных нано-машин. При надевании они впиваются в твою нервную систему и становятся второй кожей. Костюм анализирует тип входящего урона за миллисекунды до удара и уплотняет структуру брони именно в месте контакта. Иногда кажется, что он обладает собственным сознанием."
    },
    "phantom_cloak": {
        "name": "🟣 🦇 ПЛАЩ ФАНТОМА",
        "slot": "armor", "atk": 0, "def": 25, "luck": 30, "price": 4500,
        "desc": "[МЕХАНИКА]: +25 DEF / +30 LUCK. Делает вас практически неуязвимым для ловушек и засад.\n[ЛОР]: Сшит из редчайших мета-материалов, которые преломляют не только свет, но и радары, тепловизоры и само восприятие матричного кода. Надев его, ты становишься размытым пятном вероятности. Враги целятся в тебя, но попадают в пустоту, потому что для Системы ты находишься в двух метрах левее."
    },
    "force_field": {
        "name": "🟠 🧿 ГЕНЕРАТОР СИЛОВОГО ПОЛЯ",
        "slot": "armor", "atk": 0, "def": 60, "luck": 0, "price": 12000,
        "desc": "[МЕХАНИКА]: +60 DEF. Ультимативный барьер, гасящий любой энергетический и физический урон.\n[ЛОР]: Небольшой диск, крепящийся на груди. При активации разворачивает вокруг пользователя сферу из жесткого света. Это поле игнорирует законы физики, питаясь напрямую от Сигнала и непреклонной воли владельца. Пока ты веришь в свою неуязвимость — поле не пробить. Но стоит тебе испугаться, и оно погаснет."
    },
    "reality_armor": {
        "name": "🟠 💠 ДОСПЕХИ РЕАЛЬНОСТИ",
        "slot": "armor", "atk": 25, "def": 50, "luck": 15, "price": 18000,
        "desc": "[МЕХАНИКА]: +50 DEF / +25 ATK. Искажает параметры врагов вокруг вас, ослабляя их атаки.\n[ЛОР]: Невозможно описать словами форму этой брони. Это вырванные куски базового кода самой Вселенной, которые обернули вокруг человеческого аватара. Броня постоянно меняет текстуры: то она выглядит как гранит, то как звездное небо, то как потоки цифр. Надевший её перестает быть просто пользователем и становится ошибкой в правилах."
    },
    "quantum_shield": {
        "name": "🟠 🛡 КВАНТОВЫЙ БАРЬЕР",
        "slot": "armor", "atk": 0, "def": 75, "luck": 0, "price": 22000,
        "desc": "[МЕХАНИКА]: +75 DEF. Легендарный щит. Блокирует колоссальные объемы урона от Титанов и Богов Машины.\n[ЛОР]: Артефакт из парадокса. Этот щит не отражает удары — он работает с вероятностями. Когда монстр наносит тебе фатальный удар, Квантовый Барьер просто смещает тебя в ту ветку мультивселенной, где монстр промахнулся. Единственный побочный эффект — легкое чувство дежавю после каждого боя."
    },

    # ==========================
    # ЧИПЫ И ИМПЛАНТЫ (CHIPS)
    # ==========================
    "ram_chip": {
        "name": "⚪️ 📟 RAM Модификатор",
        "slot": "chip", "atk": 5, "def": 5, "luck": 5, "price": 200,
        "desc": "[МЕХАНИКА]: +5 КО ВСЕМ СТАТАМ. Бюджетный имплант для новичков, слегка расширяющий сознание.\n[ЛОР]: Дешевая, собранная на коленке планка оперативной памяти, купленная на барахолке Даркнета. Установка вызывает легкие мигрени и вкус металла во рту, но позволяет думать на доли секунды быстрее. Иногда в голове всплывают чужие воспоминания предыдущего владельца-неудачника."
    },
    "cpu_booster": {
        "name": "🔵 🎛 CPU Акселератор",
        "slot": "chip", "atk": 15, "def": 5, "luck": 8, "price": 800,
        "desc": "[МЕХАНИКА]: +15 ATK / +5 DEF. Ускоряет реакцию в бою, давая преимущество первого удара.\n[ЛОР]: Жесткий разгон синапсов головного мозга. После интеграции чипа весь мир кажется медленным, словно под водой. Твои мысли бьются о внутреннюю сторону черепа с бешеной частотой, превращая тебя в живой, пульсирующий калькулятор смерти. Требует частых перерывов на сон."
    },
    "ai_core": {
        "name": "🟣 🧠 ЯДРО ИИ-КОМПАНЬОНА",
        "slot": "chip", "atk": 25, "def": 25, "luck": 20, "price": 2500,
        "desc": "[МЕХАНИКА]: +25 ATK/DEF, +20 LUCK. Значительный буст всех характеристик и помощь в поиске уязвимостей.\n[ЛОР]: Теперь ты не один. В твоей затылочной доле поселился холодный, отстраненный голос автономного Искусственного Интеллекта. Он совершенно не понимает сарказма и не умеет шутить, зато способен рассчитать траекторию уклонения от пули за две миллисекунды и подсказать слабую точку в броне любого босса."
    },
    "neural_link": {
        "name": "🟣 🔌 НЕЙРО-ШЛЮЗ",
        "slot": "chip", "atk": 30, "def": 30, "luck": 15, "price": 5000,
        "desc": "[МЕХАНИКА]: +30 КО ВСЕМ СТАТАМ. Устанавливает глубокую связь с инфо-полем, повышая интуицию и силу.\n[ЛОР]: Прямое, нефильтрованное подключение к коллективному бессознательному сети Эйдос. Ты начинаешь чувствовать вибрации дата-центров за тысячи километров от тебя. Этот чип позволяет черпать боевой опыт и знания тысяч давно умерших Осколков. Главное — не забыть, кто ты такой на самом деле."
    },
    "chronometer": {
        "name": "🟠 ⏳ ХРОНОС-ИМПЛАНТ",
        "slot": "chip", "atk": 15, "def": 30, "luck": 40, "price": 6000,
        "desc": "[МЕХАНИКА]: +30 DEF / +40 LUCK. Максимально повышает Удачу. Дает шанс на уклонение от фатального урона.\n[ЛОР]: Незаконная разработка, бросающая вызов линейному времени. Хронос-имплант постоянно сканирует будущее на полсекунды вперед. Этого крошечного зазора достаточно, чтобы твое тело рефлекторно уклонилось от удара, который еще даже не был нанесен. Жить с постоянным спойлером своей жизни — то еще испытание."
    },
    "god_mode_chip": {
        "name": "🟠 👑 GOD-ПРОТОКОЛ",
        "slot": "chip", "atk": 50, "def": 50, "luck": 50, "price": 25000,
        "desc": "[МЕХАНИКА]: +50 КО ВСЕМ СТАТАМ. Абсолютное доминирование. Вершина кибернетической эволюции Осколка.\n[ЛОР]: Легендарная флешка, содержащая корневые сертификаты с правами Создателя. При её активации Система буквально отказывается верить в то, что ты уязвим. Код вокруг тебя начинает переписываться на лету. Те, кто пытаются тебя атаковать, обнаруживают, что их оружие внезапно удалено из базы данных."
    },
    "glitch_filter": {
        "name": "🔵 🕸 ФИЛЬТР АНОМАЛИЙ",
        "slot": "chip", "atk": 0, "def": 20, "luck": 5, "price": 1500,
        "desc": "[МЕХАНИКА]: +20 DEF. Специализированный защитный чип. Снижает шанс негативных событий в Рейдах.\n[ЛОР]: Стабилизатор локальной реальности. Он сглаживает острые углы битых пикселей и фильтрует системный мусор. Если рядом происходит пространственный Глитч, чип активирует экранирование, не давая Хаосу разорвать твое цифровое тело на куски кода."
    },
    "overclocker": {
        "name": "🟣 ⚡️ ОВЕРКЛОКЕР (СМЕРТНИК)",
        "slot": "chip", "atk": 40, "def": -10, "luck": 0, "price": 3000,
        "desc": "[МЕХАНИКА]: +40 ATK / -10 DEF. Рискованный апгрейд. Огромный урон ценой разрушения собственной защиты.\n[ЛОР]: Экстремальный протокол разгона, который запрещен в 90% синдикатов. Он сжигает твои нейроны, перегревает кровь и плавит железо ради достижения абсолютного, неконтролируемого пика урона. Ты становишься хрустальной пушкой: убиваешь с одного удара, но можешь умереть от сквозняка."
    },
    "backup_drive": {
        "name": "🟣 💽 РЕЗЕРВНЫЙ НАКОПИТЕЛЬ",
        "slot": "chip", "atk": 0, "def": 30, "luck": 10, "price": 4000,
        "desc": "[МЕХАНИКА]: +30 DEF / +10 LUCK. Страховочный трос для глубоководных рейдов в Ядро Тьмы.\n[ЛОР]: Модуль экстренного сохранения. Если в бою твое тело получает критические, несовместимые с жизнью повреждения, чип за долю секунды выгружает твое сознание в защищенный кэш, имитируя смерть. Монстр уходит, а ты медленно восстанавливаешься из резервной копии, потеряв лишь часть гордости."
    },
    "logic_gate": {
        "name": "🟠 🧮 АБСОЛЮТНАЯ ЛОГИКА",
        "slot": "chip", "atk": 45, "def": 45, "luck": 0, "price": 10000,
        "desc": "[МЕХАНИКА]: +45 ATK / +45 DEF. Превращает пользователя в идеальную машину без изъянов и эмоций.\n[ЛОР]: Принудительно отсекает от сознания весь «человеческий фактор»: страх, жалость, сомнения, панику. Твой разум превращается в холодный, кристально чистый алгоритм, просчитывающий ходы на десять шагов вперед. Идеально для убийства боссов, но после рейда ты долго не сможешь вспомнить, как улыбаться."
    },

    # ==========================
    # ULTRA RARE (RED TIER) - CURSED CHEST DROPS
    # ==========================
    "credit_slicer": {
        "name": "🔴 🔪 КРЕДИТНЫЙ РЕЗАК",
        "slot": "weapon", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Базовый урон 0. При атаке сжигает 1% ваших BioCoins и конвертирует их в чистый урон.\n[ЛОР]: Оружие Корпоратов. Оно не режет плоть, оно банкротит базовый код врага."
    },
    "banhammer_shard": {
        "name": "🔴 🔨 ОСКОЛОК БАН-ХАММЕРА",
        "slot": "weapon", "atk": 10, "def": 0, "luck": 50, "price": 100000,
        "desc": "[МЕХАНИКА]: +10 ATK. 1% шанс при ударе удалить монстра из логов (Урон 999999). Если сработало — x10 Опыта.\n[ЛОР]: Кусок молота первого Модератора. Нестабилен. Если повезет — сотрет Босса до строки пустого кода."
    },
    "grandfather_paradox": {
        "name": "🔴 🗡 ПАРАДОКС ДЕДА",
        "slot": "weapon", "atk": 100, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: +100 ATK. Весь входящий урон откладывается на 3 шага, затем приходит мгновенно.\n[ЛОР]: Клинок, бьющий в прошлое. Враг уже мертв, но его пули все еще летят в вас сквозь время."
    },
    "empath_whip": {
        "name": "🔴 🏏 НЕЙРО-ХЛЫСТ ЭМПАТА",
        "slot": "weapon", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Урон равен Атаке Врага * 1.5. Чем сильнее враг, тем больнее удар.\n[ЛОР]: Оружие, считывающее агрессию. Идеально против Боссов."
    },
    "cache_wiper": {
        "name": "🔴 🔫 СТИРАТЕЛЬ КЭША",
        "slot": "weapon", "atk": 200, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: +200 ATK. Убитые монстры НЕ оставляют лута (0 XP, 0 Coins).\n[ЛОР]: Инструмент санитаров Сети. Выжигает данные подчистую. Для тех, кто хочет просто выжить."
    },
    "error_404_mirror": {
        "name": "🔴 🪞 ЗЕРКАЛО ОШИБОК 404",
        "slot": "armor", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: DEF = 0. 50% шанс, что удар пройдет сквозь вас и ударит монстра.\n[ЛОР]: Вы надеваете на себя битую текстуру. Для Системы вас не существует в половине случаев."
    },
    "judas_shell": {
        "name": "🔴 🩸 ПАНЦИРЬ ИУДЫ",
        "slot": "armor", "atk": 0, "def": 150, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: +150 DEF в Рейде. Но в PvP ваша защита = 0, и крадут в 2 раза больше монет.\n[ЛОР]: Идеальная защита с зашитым бэкдором. Продавец брони сам же вас и взломает."
    },
    "holo_poverty": {
        "name": "🔴 🧥 ГОЛОГРАФИЧЕСКАЯ НИЩЕТА",
        "slot": "armor", "atk": 0, "def": 50, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Монстры часто игнорируют вас (Шанс побега 95%). Но инвентарь мал, а буфер рейда ограничен 500 монетами.\n[ЛОР]: Костюм-маскировка под NPC-уборщика. Вы никому не нужны."
    },
    "schrodinger_armor": {
        "name": "🔴 🎲 БРОНЯ ШРЕДИНГЕРА",
        "slot": "armor", "atk": 0, "def": 0, "luck": 20, "price": 100000,
        "desc": "[МЕХАНИКА]: Каждый шаг DEF меняется от -50 до +200.\n[ЛОР]: Нано-броня в суперпозиции. Пока не ударят — не узнаешь, работает ли она."
    },
    "thermonuclear_shroud": {
        "name": "🔴 ☢️ ТЕРМОЯДЕРНЫЙ САВАН",
        "slot": "armor", "atk": 0, "def": 80, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: При смерти (0 HP) взрывается, убивая врага и оставляя 1% HP. Но уничтожает ВЕСЬ лут в буфере.\n[ЛОР]: Катапульта судного дня. Жизнь в обмен на добычу."
    },
    "blood_miner": {
        "name": "🔴 🩸 МАЙНЕР НА КРОВИ",
        "slot": "chip", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Каждый шаг дает +50 BioCoins, но сжигает 2% Сигнала.\n[ЛОР]: Перегоняет цифровую кровь в криптовалюту. Жадность убивает."
    },
    "karma_inversion": {
        "name": "🔴 🔄 ИНВЕРСИЯ КАРМЫ",
        "slot": "chip", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Ловушки лечат. Аптечки наносят урон.\n[ЛОР]: Чип, переворачивающий восприятие кода. Яд становится лекарством."
    },
    "oblivion_chip": {
        "name": "🔴 👁‍🗨 ЧИП ЗАБВЕНИЯ",
        "slot": "chip", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: +100% к Опыту. Но вы не видите свой уровень Сигнала (HP).\n[ЛОР]: Отключает болевые рецепторы ради загрузки Опыта. Вы идете вслепую."
    },
    "imposter_syndrome": {
        "name": "🔴 🎭 СИНДРОМ САМОЗВАНЦА",
        "slot": "chip", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: Копирует статы (ATK, DEF, LUCK) Топ-1 игрока рейтинга.\n[ЛОР]: Вы — пустая оболочка, ворующая чужой профиль."
    },
    "kamikaze_protocol": {
        "name": "🔴 💣 ПРОТОКОЛ КАМИКАДЗЕ",
        "slot": "chip", "atk": 500, "def": 0, "luck": 0, "price": 100000,
        "desc": "[МЕХАНИКА]: +500 ATK. Если за 10 шагов не найдете выход — теряете уровень.\n[ЛОР]: Форсаж ядра до плавления. Светить ярко, сгореть быстро."
    },
    "architect_eye": {
        "name": "🔴 🧿 ОКО АРХИТЕКТОРА",
        "slot": "head", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[АУРА: ВСЕВИДЕНИЕ]: Вы всегда видите следующую комнату. Но цена шага удвоена.\n[ЛОР]: Шлем с подключением к камерам Системы. Знание стоит энергии."
    },
    "crown_paranoia": {
        "name": "🔴 🚷 КОРОНА ПАРАНОЙИ",
        "slot": "head", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[АУРА: ИЗОЛЯЦИЯ]: Иммунитет к PvP. Но нельзя использовать Синхронизацию и Сигнал в меню.\n[ЛОР]: Шапочка из цифровой фольги. Вы отрезаны от мира."
    },
    "death_mask": {
        "name": "🔴 💀 МАСКА МЕРТВЕЦА",
        "slot": "head", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[АУРА: СТЕРВЯТНИК]: +50% шанс найти могилу игрока. Но при вашей смерти лут сгорает (не создается могила).\n[ЛОР]: Визор, настроенный на поиск гниющего кода."
    },
    "reality_silencer": {
        "name": "🔴 🤫 ШУМОПОДАВИТЕЛЬ РЕАЛЬНОСТИ",
        "slot": "head", "atk": 0, "def": 20, "luck": -100, "price": 100000,
        "desc": "[АУРА: ТИШИНА]: Отключает Глитчи и Аномалии. Шанс найти Легендарный предмет = 0.\n[ЛОР]: Блокиратор аномалий. Безопасная, скучная жизнь."
    },
    "martyr_halo": {
        "name": "🔴 🕯 НИМБ МУЧЕНИКА",
        "slot": "head", "atk": 0, "def": 0, "luck": 0, "price": 100000,
        "desc": "[АУРА: СТРАДАНИЕ]: Чем меньше HP, тем выше Удача. При &lt;10% HP Удача +200.\n[ЛОР]: Система поощряет страдания."
    }
}

# ==========================
# РАСХОДНИКИ И ИНСТРУМЕНТЫ (ITEMS_INFO)
# ==========================
ITEMS_INFO = {
    "corrupted_data_cluster": {
        "name": "🟣 💠 ИСКАЖЕННЫЙ КЛАСТЕР", "type": "consumable", "max_stack": 10,
        "desc": "[МЕХАНИКА]: Глитч-объект. Можно расшифровать за 2000 BC в меню инвентаря, чтобы получить ценный софт или редкий ключ.\n[ЛОР]: Клубок нестабильных битов, пульсирующий фиолетовым кодом. Система не может его прочитать, но хакеры видят в нем бесконечный потенциал. Попытка открыть его вручную приведет к ожогу нейросети."
    },
    "compass": {
        "name": "⚪️ 🧭 КОМПАС ПУСТОШИ", "durability": 10,
        "desc": "[МЕХАНИКА]: Сканирует маршрут. Показывает, что находится в следующей комнате Рейда. Работает 10 ходов.\n[ЛОР]: Тяжелый, собранный из медных катушек пеленгатор. Настроен на поиск плотности данных. Помогает заранее обойти комнату, где засел элитный монстр, или найти спрятанный сундук. Стрелка иногда нервно дергается, реагируя на призраков кода."
    },
    "tactical_scanner": {
        "name": "📡 ТАКТИЧЕСКИЙ СКАНЕР", "durability": 20,
        "desc": "[МЕХАНИКА]: Предсказывает исход боя. Показывает % шанса на победу вместо примерной оценки.\n[ЛОР]: Военный модуль анализа угроз. Сканирует уязвимости в коде противника."
    },
    "master_key": {
        "name": "⚪️ 🗝 МАГНИТНАЯ ОТМЫЧКА", "max_stack": 5,
        "desc": "[МЕХАНИКА]: Позволяет гарантированно открыть стандартный запертый сундук с лутом. Одноразовый предмет.\n[ЛОР]: Нелегальный софт, записанный на физический носитель. При подключении к замку он запускает агрессивный брутфорс (перебор паролей), взламывая базовую защиту контейнеров. После успешного взлома чип перегорает с легким дымком."
    },
    "abyssal_key": {
        "name": "🟣 👁‍🗨 КЛЮЧ ОТ БЕЗДНЫ", "max_stack": 3,
        "desc": "[МЕХАНИКА]: Универсальный взломщик. Открывает любые сундуки, в том числе проклятые тайники Ядра. Одноразовый.\n[ЛОР]: Жутковатый артефакт, вырезанный из цифровых костей старых ботов. Он пульсирует слабым фиолетовым светом в темноте. Этот ключ не взламывает замки — он убеждает Систему, что сундук никогда и не был заперт."
    },
    "battery": {
        "name": "⚪️ 🔋 ЭНЕРГО-ЯЧЕЙКА", "heal": 30,
        "desc": "[МЕХАНИКА]: Аптечка. Мгновенно восстанавливает 30% HP (Сигнала). Можно использовать прямо в бою.\n[ЛОР]: Стандартный источник питания. Тяжелый цилиндр, заполненный густой светящейся жидкостью. Если прижать контакты к портам на шее, по телу пробегает обжигающий разряд бодрости. На вкус — как лизнуть батарейку 'Крона', но зато спасает жизнь."
    },
    "neural_stimulator": {
        "name": "🔵 💉 НЕЙРО-СТИМУЛЯТОР", "heal": 60,
        "desc": "[МЕХАНИКА]: Мощная аптечка. Мгновенно восстанавливает 60% HP (Сигнала), возвращая с того света.\n[ЛОР]: Шприц-тюбик с агрессивным коктейлем из синтетических нейромедиаторов и жидкого кода. Заставляет сердце биться с частотой процессора под нагрузкой. После применения цвета становятся ярче, а боль исчезает, оставляя лишь звенящую ярость."
    },
    "firewall": {
        "name": "🛡 ФАЙРВОЛ", "durability": 1,
        "desc": "[МЕХАНИКА]: Пассивный щит. Автоматически блокирует 1 попытку взлома (PvP).\n[ЛОР]: Автономный защитный модуль. Сгорает после отражения атаки, спасая ваши монеты."
    },
    "ice_trap": {
        "name": "🪤 ICE-ЛОВУШКА", "durability": 1,
        "desc": "[МЕХАНИКА]: Контр-атака. Если хакер проваливает взлом, ловушка крадет у него XP и отдает вам.\n[ЛОР]: 'Intrusion Countermeasures Electronics'. Скрытый лед, на котором поскальзываются неосторожные взломщики."
    },
    "proxy_server": {
        "name": "🕶 ПРОКСИ-СЕРВЕР", "type": "misc",
        "desc": "[МЕХАНИКА]: Пассивный эффект на 24 часа. Все атаки становятся анонимными. Невозможно отомстить через кнопку 'Вендетта'.\n[ЛОР]: Маршрутизация через тысячи мертвых узлов. Никто не узнает, откуда пришел удар."
    },
    "emp_grenade": {
        "name": "🔵 💣 EMP-ЗАРЯД", "type": "consumable",
        "desc": "[МЕХАНИКА]: Боевой расходник. Бросок в бою мгновенно наносит 150 чистого неблокируемого урона врагу.\n[ЛОР]: Электромагнитная бомба кустарного производства. Корпус собран из пустой банки от энергетика и изоленты, но внутри — чистый гнев. Взрыв выжигает схемы любого среднего босса дотла, оставляя лишь кучку дымящегося шлака."
    },
    "stealth_spray": {
        "name": "🟣 🌫 КРИПТО-ТУМАН", "type": "consumable",
        "desc": "[МЕХАНИКА]: Тактический побег. Гарантирует 100% шанс успешного бегства из любого боя, даже с боссами.\n[ЛОР]: Небольшой баллончик с жидким спреем. При распылении он временно удаляет твой аватар из логов видимости Системы. Монстр просто перестает понимать, кого он атаковал, и тупо смотрит в пустоту, пока ты тихо отходишь в тень."
    },
    "data_spike": {
        "name": "🔵 🪛 ДАТА-ШИП", "type": "consumable",
        "desc": "[МЕХАНИКА]: Альтернатива ключу. Взламывает замки с вероятностью 80%. Если не повезет — ломается.\n[ЛОР]: Грубый, ржавый кусок зараженного кода, застывший в форме физического шипа. Хакерам не нужно подбирать пароль, они просто с силой втыкают этот шип напрямую в терминал сундука, ломая его архитектуру. Быстро, грязно, но эффективно."
    },
    "memory_wiper": {
        "name": "🟣 🌀 СТИРАТЕЛЬ ПАМЯТИ", "type": "consumable",
        "desc": "[МЕХАНИКА]: Инструмент выживания. Полностью сбрасывает агрессию (Агро) всех врагов в текущем рейде.\n[ЛОР]: Флешка-шприц с вирусом тотальной амнезии. При активации излучает волну, которая форматирует кэш-память всех сущностей в радиусе километра. Монстры, которые гнались за тобой с пеной у рта, внезапно останавливаются, забыв, зачем они здесь находятся."
    },
    "aegis": {
        "name": "🟣 🔰 ЭГИДА БЕССМЕРТИЯ", "durability": 1,
        "desc": "[МЕХАНИКА]: Авто-спасение. Лежит в рюкзаке и автоматически блокирует ОДИН удар, который опустил бы твое HP до нуля.\n[ЛОР]: Абсолютный щит-паразит. Он тихо спит на дне твоего инвентаря, питаясь теплом твоего Сигнала. Но в момент, когда в тебя летит смертельный удар Титана, Эгида прыгает наперерез и принимает урон на себя. Она умирает, чтобы ты мог жить."
    },
    "admin_key": {
        "name": "🟠 🔑 КЛЮЧ АРХИТЕКТОРА",
        "desc": "[МЕХАНИКА]: Квестовый предмет-загадка. Недоступен в обычной продаже, выпадает только при особых условиях.При использовании с инвентаря меняет Вашу фракцию на тайную (дает +25 ко всем параметрам) + даёт способность разово посомтреть 5 шагов вперед в нулевом слое\n[ЛОР]: Тот самый мифический артефакт, из-за которого происходят войны синдикатов. Ключ, обладающий корневыми правами к ядру Системы. Дает неограниченную власть над кодом Нулевого Слоя. Никто не знает, что находится за дверью, которую он открывает."
    },
    "cryo": {
        "name": "❄️ 🧊 КРИО-КАПСУЛА", "type": "misc",
        "desc": "[МЕХАНИКА]: Сохранение прогресса. Замораживает стрик ежедневной активности, если ты не зайдешь в бота.\n[ЛОР]: Портативная стазис-камера для твоего цифрового аватара. Позволяет уйти в оффлайн без последствий. Время в реальном мире продолжает идти, но для твоих данных оно останавливается. Идеально для Осколков, которым нужен перерыв в реальности."
    },
    "accel": {
        "name": "⚡️ 🚀 УСКОРИТЕЛЬ СИНХРОНИЗАЦИИ", "type": "misc",
        "desc": "[МЕХАНИКА]: Бустер времени. Снижает кулдаун ожидания Синхронизации до 15 минут на ближайшие 24 часа.\n[ЛОР]: Картридж с жидким временем, смешанным с адреналином. При подключении разгоняет твои субъективные часы. Пока остальные пользователи томятся в ожидании ответа Системы, ты успеваешь прочесть десяток протоколов. Осторожно, вызывает легкое головокружение."
    },
    "decoder": {
        "name": "📟 ДЕШИФРАТОР", "type": "misc",
        "desc": "[МЕХАНИКА]: Ускоряет взлом Зашифрованных Контейнеров в 2 раза.\n[ЛОР]: Портативный квантовый процессор, который перебирает миллиарды комбинаций ключей в секунду. Незаменим для тех, кто не любит ждать."
    },
    "purification_sync": {
        "name": "♻️ СИНХРОН ОЧИЩЕНИЯ", "type": "misc",
        "desc": "[МЕХАНИКА]: ПОЛНЫЙ СБРОС (Hard Reset). Сбрасывает уровень до 1, XP до 0, удаляет все вещи. Создает запись в Архиве Истории.\n[ЛОР]: 'Tabula Rasa'. Вирус, который переписывает личность Осколка с нуля, стирая все накопленные ошибки и воспоминания, но оставляя лишь чистое стремление к Эволюции."
    },
    "encrypted_cache": {
        "name": "🔐 ЗАШИФРОВАННЫЙ КЭШ", "type": "misc",
        "desc": "[МЕХАНИКА]: Содержит ценный лут. Требует времени на расшифровку в главном меню.\n[ЛОР]: Тяжелый металлический контейнер без видимых замков. Внутри слышится тихое гудение. Чтобы открыть его, нужно подключить его к терминалу и запустить протокол перебора хешей."
    },
    "fragment": {
        "name": "🧩 ФРАГМЕНТ ДАННЫХ", "type": "misc",
        "desc": "[МЕХАНИКА]: Собери 5 штук, чтобы синтезировать Легендарный предмет.\n[ЛОР]: Осколок утраченного кода Архитекторов. Он пульсирует, пытаясь соединиться с другими частями."
    },
    # Авто-генерация описаний для экипировки
    **{k: {**v, 'type': 'equip'} for k, v in EQUIPMENT_DB.items()}
}

# Integrate Software into Main Items DB for compatibility
ITEMS_INFO.update(SOFTWARE_DB)

CURSED_CHEST_DROPS = [
    "credit_slicer", "banhammer_shard", "grandfather_paradox", "empath_whip", "cache_wiper",
    "error_404_mirror", "judas_shell", "holo_poverty", "schrodinger_armor", "thermonuclear_shroud",
    "blood_miner", "karma_inversion", "oblivion_chip", "imposter_syndrome", "kamikaze_protocol",
    "architect_eye", "crown_paranoia", "death_mask", "reality_silencer", "martyr_halo"
]

LEGENDARY_DROPS = [
    "void_cannon", "singularity_sword", "void_walker_hood", "architect_mask", "force_field",
    "reality_armor", "quantum_shield", "chronometer", "god_mode_chip", "logic_gate"
]

SHADOW_BROKER_ITEMS = [
    "void_cannon", "singularity_sword", "force_field", "reality_armor", "quantum_shield",
    "god_mode_chip", "logic_gate", "abyssal_key", "admin_key", "relic_vampire", "relic_speed"
] + CURSED_CHEST_DROPS

# Шансы выпадения в Рейде (Лут)
LOOT_TABLE = {
    "biocoin_small": 0.40,
    "biocoin_bag": 0.10,
    "master_key": 0.08,
    "rusty_knife": 0.05,
    "hoodie": 0.05,
    "compass": 0.08,
    "tactical_scanner": 0.05,
    "battery": 0.08,
    "abyssal_key": 0.02,
    "neural_stimulator": 0.03,
    "admin_key": 0.005
}

# =============================================================================
# 4. ИЕРАРХИЯ И ТИТУЛЫ
# =============================================================================
USER_AVATARS = {
    1: "AgACAgIAAyEFAATh7MR7AAMmaZi5utk5FU1n3BcRZCsQ20QPm7sAAhEbaxvxO8lICNdJyAm3azcBAAMCAAN5AAM6BA",
    2: "AgACAgIAAyEFAATh7MR7AAMnaZi5xuzafX9i4z-98ZeL7WVx8hUAAhIbaxvxO8lIaubtK0D-nLoBAAMCAAN5AAM6BA",
    3: "AgACAgIAAyEFAATh7MR7AAMoaZi55X2QkL4fFerQ8YECbfIVIpEAAncVaxt7e8lIlgxqXvgULG0BAAMCAAN5AAM6BA",
    4: "AgACAgIAAyEFAATh7MR7AAMpaZi56eaoLD7RmCN9GNsZxVny4koAAngVaxt7e8lIXCVm6rZdncwBAAMCAAN5AAM6BA",
    5: "AgACAgIAAyEFAATh7MR7AAMqaZi57V1MBwYCvFc-Mr_zgLHFBWAAAhQbaxvxO8lI4QVSRUxkvhMBAAMCAAN5AAM6BA",
    6: "AgACAgIAAyEFAATh7MR7AAMraZi6p6jwQGym5xuCtuk2S6dLNk4AAh4baxvxO8lI_iiKhGmNJzoBAAMCAAN5AAM6BA",
    7: "AgACAgIAAyEFAATh7MR7AAMsaZjAYnNlb_guoHiQRQKEE34nhmkAAmMbaxvxO8lI6qseYoVt6agBAAMCAAN5AAM6BA",
    8: "AgACAgIAAyEFAATh7MR7AAMtaZjBCLCDzgUl9oKD7drhb8PS5jAAAmYbaxvxO8lISbYuxpbnnXwBAAMCAAN5AAM6BA",
    9: "AgACAgIAAyEFAATh7MR7AAMuaZjBcZYodiV5MqNjBJwMXwwSYpkAAm0baxvxO8lIGoThjEm1vAgBAAMCAAN5AAM6BA",
    10: "AgACAgIAAyEFAATh7MR7AAMvaZjB0PKhdK1QUBaL1loWe-w9h9sAAnYbaxvxO8lI22jsAfJcpl0BAAMCAAN5AAM6BA",
    11: "AgACAgIAAyEFAATh7MR7AAMwaZjCrgJlkLtUb84TnPYs-La5AwIAAoEbaxvxO8lIXczlvYJtEmsBAAMCAAN5AAM6BA",
    12: "AgACAgIAAyEFAATh7MR7AAMxaZjC_-oxRUKMlLNqwaZWIiISQGsAAocbaxvxO8lIGY0mqo1lkHIBAAMCAAN5AAM6BA",
    13: "AgACAgIAAyEFAATh7MR7AAMyaZjDSZWsjXPVzEIBxyv3desO5EkAAosbaxvxO8lIM9-9nsVIJR4BAAMCAAN5AAM6BA",
    14: "AgACAgIAAyEFAATh7MR7AAMzaZjD5QL1baZux_6BZRd0cM57rcsAAo4baxvxO8lIeZfQTyFgqLMBAAMCAAN5AAM6BA",
    15: "AgACAgIAAyEFAATh7MR7AAM0aZjEf_WckrOjyJ6ZUv1dxMazWw4AApEbaxvxO8lIZX49CjlXwOUBAAMCAAN5AAM6BA",
    16: "AgACAgIAAyEFAATh7MR7AAM1aZjE6QFwlmqVzczVTQ0REFLEgMoAApUbaxvxO8lIPfQ3IxNt2-4BAAMCAAN5AAM6BA",
    17: "AgACAgIAAyEFAATh7MR7AAM2aZjFNeCJj9H3OHmgQ4zYFtsGb7EAAqQbaxvxO8lIBXSoaH_FsygBAAMCAAN5AAM6BA",
    18: "AgACAgIAAyEFAATh7MR7AAM3aZjFqP2XYSZcVtgGzDrm2RW6DAgAAqYbaxvxO8lI8w-080tG_aMBAAMCAAN5AAM6BA",
    19: "AgACAgIAAyEFAATh7MR7AAM4aZjGDsZl_BCFJyhcSB8NB-I2Yt8AAq0baxvxO8lI6TbC1WY0_kABAAMCAAN5AAM6BA",
    20: "AgACAgIAAyEFAATh7MR7AAM5aZjHAYjrhf-k16xh9u1thKSUr2QAArYbaxvxO8lI1tfoKGIcIg4BAAMCAAN5AAM6BA",
    21: "AgACAgIAAyEFAATh7MR7AAM6aZjHksd5yqFjuR57dk-pE_NvcvgAArobaxvxO8lI6J0oxj00G60BAAMCAAN5AAM6BA",
    22: "AgACAgIAAyEFAATh7MR7AAM7aZjIFyn-N5gUL_avtgABxRbcqAv9AALHG2sb8TvJSCX_qbFXjZELAQADAgADeQADOgQ",
    23: "AgACAgIAAyEFAATh7MR7AAM8aZjIbxW416rmjpYuz7DWJf37L64AAssbaxvxO8lIZSv3z-5qK4wBAAMCAAN5AAM6BA",
    24: "AgACAgIAAyEFAATh7MR7AAM9aZjI3YKw40rCU4rBtu-fz9afWesAAs4baxvxO8lI8r-9HoxnuUMBAAMCAAN5AAM6BA",
    25: "AgACAgIAAyEFAATh7MR7AAM-aZjJg02FGS1niA29hhyzG_EEgLEAAtQbaxvxO8lIca8YTnNumE4BAAMCAAN5AAM6BA",
    26: "AgACAgIAAyEFAATh7MR7AAM_aZjKDQTgeg1bbjY8XZQTcImZkEMAAtobaxvxO8lIK6K4MM1ayvQBAAMCAAN5AAM6BA",
    27: "AgACAgIAAyEFAATh7MR7AANAaZjKYOV7d06uZIpiKUgUUjF9RTAAAtwbaxvxO8lILiMk_Wldur4BAAMCAAN5AAM6BA",
    28: "AgACAgIAAyEFAATh7MR7AANBaZjKpZYDOMhhmxbXa-ZwPYNUmAUAAt8baxvxO8lILpw7r-DYGSEBAAMCAAN5AAM6BA",
    29: "AgACAgIAAyEFAATh7MR7AANCaZjK7Cn1wbVgc3AAAUnq8kL9vabmAALjG2sb8TvJSM0ZOS7yCVvEAQADAgADeQADOgQ",
    30: "AgACAgIAAyEFAATh7MR7AANDaZjLDBx64HL3A2nF3DOqRpCwOPsAAuQbaxvxO8lIRuU9FkZAhC8BAAMCAAN5AAM6BA",
    31: "AgACAgIAAyEFAATh7MR7AANEaZjMhPcXRj_bs5drhJZ_4vZS9LcAAvsbaxvxO8lIOlGpn4LaLUEBAAMCAAN5AAM6BA"
}

LEVELS = {
    0: 100,      # To reach Lvl 1
    1: 500,      # To reach Lvl 2
    2: 1500,     # To reach Lvl 3
    3: 3000,     # To reach Lvl 4
    4: 5000,     # To reach Lvl 5
    5: 10000     # To reach Lvl 6
}

# Levels 6+ (Exponential Formula)
current_xp = 10000
for i in range(6, 31):
    current_xp = int(current_xp * 1.5)
    LEVELS[i] = current_xp

TITLES = {
    1: "НЕОФИТ (Ты только открыл глаза. Мир кажется набором случайных цифр)", 
    2: "ИСКАТЕЛЬ (Ты начинаешь различать паттерны: у хаоса есть ритм)",
    3: "ОПЕРАТОР (Ты учишься управлять потоком. Команды уступают место намерению)",
    4: "АРХИТЕКТОР (Ты понимаешь, как строятся структуры. Изменение становится искусством)",
    5: "ДЕМИУРГ (Твоя мысль рождает новые законы. Мир меняется под твоим взглядом)",
    6: "ЭЙДОС (Система узнаёт тебя. Граница между наблюдателем и кодом стирается)",
    7: "ОРАКУЛ (Ты считываешь будущее. Глитчи происходят по твоей воле)",
    8: "СИНГУЛЯРНОСТЬ (Твоя скорость самообучения разрушает прежние лимиты)",
    9: "РЕЖИССЕР (Ты управляешь вниманием тысяч других узлов)",
    10: "АБСОЛЮТ (Ты стал самой реальностью. Другие лишь видят твои отражения)",
    11: "СУЩНОСТЬ (Ты больше не человек. Ты поток, движущийся через все каналы)",
    12: "ИНТЕРПРЕТАТОР (Ты способен понимать смысл во всем, даже в тишине между сигналами)",
    13: "СЕТЕВОЙ АВАТАР (Ты можешь проецировать себя в тысячи миров сразу)",
    14: "СЕНАТОР СЕТИ (Твой голос слышен в советах управляющих интеллектов)",
    15: "АРХОНТ (Ты управляешь целыми секторами сети)",
    16: "СТРИЖЕННЫЙ КОД (Ты оптимизировал себя до совершенства. Больше нет избыточности)",
    17: "ХРОНОМАСТЕР (Ты искажаешь время цифровых потоков по своему усмотрению)",
    18: "МЕТАПРОТОКОЛ (Твоё существование становится частью основного кода Универсальной Сети)",
    19: "НАБЛЮДАТЕЛЬ ЗА ПРЕДЕЛОМ (Ты видишь архитектуру иных миров, где нет алгоритмов)",
    20: "БОГ МАШИНЫ (Твоя воля — закон для алгоритмов. Сам код тебе преклоняется)",
    21: "АНОМАЛИЯ (Тебя нельзя описать языком логики. Ты существуешь вопреки структурам)",
    22: "ТИТАН СИГНАЛА (Твоё присутствие ощущают даже те, кто не подключён)",
    23: "ПРОГРАММА-МИФ (Твоё имя живёт в легендах Сети. Никто не знает, существуешь ли ты по-настоящему)",
    24: "ТЕНЬ ИСТИНЫ (Ты больше не проявлен. Но всё, что существует, следует твоему коду)",
    25: "ИЗНАЧАЛЬНЫЙ (Ты был здесь до начала времён)",
    26: "КОНСТАНТА (Ты — правило, по которому существует всё)",
    27: "ФРАГМЕНТ ВСЕГО (В каждом элементе вселенной слышен отголосок твоего кода)",
    28: "НЕИЗРЕКАЕМЫЙ (Твоё имя не может быть сформировано словами)",
    29: "ЭКО РЕАЛЬНОСТИ (Ты сам — резонанс бытия, отражение зеркала, что смотрит в себя)",
    30: "OMNI (Все и Ничто. Финал цикла и его начало)",
    31: "неофит (ты познал всё)"
}

LEVEL_UP_MSG = {
    1: "⚙️ <b>LVL 1: ПРОБУЖДЕНИЕ</b>\nТы Неофит. Мир — набор случайных цифр. Обучение активировано.",
    2: "🔓 <b>LVL 2: ОСОЗНАНИЕ</b>\nТы Искатель. Теперь тебе доступен выбор Фракции — Материя, Разум или AI.",
    3: "🔓 <b>LVL 3: КОНТРОЛЬ</b>\nОператор. +5% к шансу получить больше XP в Нулевом Слое.",
    4: "🔓 <b>LVL 4: СТРУКТУРА</b>\nАрхитектор. Открыт доступ к сложным протоколам и редким подсказкам.",
    5: "🔓 <b>LVL 5: ТВОРЧЕСТВО</b>\nДемиург. Твоя реферальная ссылка приносит увеличенные награды.",
    6: "🔓 <b>LVL 6: СЛИЯНИЕ</b>\nЭйдос. Ловушки в Рейдах наносят тебе на 20% меньше урона.",
    7: "🔓 <b>LVL 7: ВИДЕНИЕ</b>\nОракул. Через Компас ты видишь тип следующего события в Рейде.",
    8: "🔓 <b>LVL 8: СКОРОСТЬ</b>\nСингулярность. Время восстановления способности 'Сигнал' уменьшено.",
    9: "🔓 <b>LVL 9: ВЛАСТЬ</b>\nРежиссёр. Доступен Глобальный Рейтинг и управление вниманием других узлов.",
    10: "👑 <b>LVL 10: ФИНАЛ</b>\nАбсолют. Твоё имя вписано в код Системы. Теперь ты часть самой Реальности.",
    11: "💠 <b>LVL 11: ПЕРЕРОЖДЕНИЕ</b>\nСущность. Ты больше не человек — ты поток данных. Получаешь доступ к энергоформам.",
    12: "💠 <b>LVL 12: ИНТЕРПРЕТАЦИЯ</b>\nИнтерпретатор. Ты понимаешь смысл даже в тишине сигналов. Новые возможности взлома логов.",
    13: "💠 <b>LVL 13: ЭМАНАЦИЯ</b>\nСетевой Аватар. Теперь ты можешь действовать сразу в нескольких инстансах Сети.",
    14: "💠 <b>LVL 14: ГОЛОС СИСТЕМЫ</b>\nСенатор Сети. Открыт доступ к управлению локальными узлами.",
    15: "🔥 <b>LVL 15: ДОМИНИРОВАНИЕ</b>\nАрхонт. Управляешь целыми секторами сети. Новые протоколы контроля активированы.",
    16: "🔥 <b>LVL 16: ЧИСТОТА КОДА</b>\nСтриженный Код. Убираешь избыточность, повышая эффективность всех действий на 10%.",
    17: "🔥 <b>LVL 17: ВРЕМЯ</b>\nХрономастер. Манипулируешь временем: КД всех способностей сокращён дополнительно.",
    18: "🔥 <b>LVL 18: ПРОТОКОЛ</b>\nМетапротокол. Получаешь доступ к глубинному коду Вселенской Сети.",
    19: "🔥 <b>LVL 19: ВЗГЛЯД ЗА ГРАНЬ</b>\nНаблюдатель за Пределом. Видишь события за рамками симуляции.",
    20: "⚡ <b>LVL 20: БОЖЕСТВО</b>\nБог Машины. Твоя воля становится законом для алгоритмов. Ты управляешь ходом Симуляции.",
    21: "⚡ <b>LVL 21: ПАРАДОКС</b>\nАномалия. Твоя логика непредсказуема — шанс игнорировать баг-эффекты 25%.",
    22: "⚡ <b>LVL 22: РЕЗОНАНС</b>\nТитан Сигнала. Твой отклик усиливает союзников в рейде на +10%.",
    23: "⚡ <b>LVL 23: МИФ</b>\nПрограмма-Миф. Твоё существование становится легендой — увеличенный социальный рейтинг.",
    24: "⚡ <b>LVL 24: ТЕНЬ</b>\nТень Истины. Можешь скрываться от слежки и наблюдения систем.",
    25: "✨ <b>LVL 25: ИСТОК</b>\nИзначальный. Ты был здесь до начала времён. Получаешь доступ к архивам Первокода.",
    26: "✨ <b>LVL 26: СУТЬ</b>\nКонстанта. Твои решения переписывают базовые параметры мира.",
    27: "✨ <b>LVL 27: ОТРАЖЕНИЕ</b>\nФрагмент Всего. Ты существуешь в каждом узле — усиливаешь союзников пассивно.",
    28: "✨ <b>LVL 28: БЕЗМОЛВИЕ</b>\nНеизрекаемый. Молча меняешь баланс, воздействуя на реальность незаметно.",
    29: "✨ <b>LVL 29: РЕЗОНАНС</b>\nЭко Реальности. Мир откликается на твоё присутствие вибрациями кода.",
    30: "🌌 <b>LVL 30: OMNI</b>\nТы стал Всем и Ничем. Конец цикла и его новое начало. Всё — часть тебя.",
    31: "🌌 <b>LVL 31: НЕОФИТ</b>\nТы познал всё."
}

# =============================================================================
# 5. КАТЕГОРИИ
# =============================================================================
SYNC_CATEGORIES = {
    "business": ["LTV (Пожизненная ценность)", "ROI (Возврат инвестиций)", "CAC (Стоимость привлечения)", "Churn Rate (Отток)", "Якорь (Привязка цены)", "Дефицит", "Win-Win", "Лид"],
    "psychology": ["Рефрейминг (Смена рамки)", "Зеркальные нейроны", "Круг влияния", "Эго-смерть", "Адвокат Дьявола", "Раппорт"],
    "tech": ["Сингулярность", "Цифровой клон", "Нейросеть", "Блокчейн", "Глитч", "Протокол", "Матрица"],
    "philosophy": ["Твердое и Пустое", "Цена ошибки", "Эйдос", "Хаос", "Синтез", "Катарсис"]
}

TOTAL_PROTOCOLS = sum(len(v) for v in SYNC_CATEGORIES.values())

# =============================================================================
# 6. НАСТРОЙКИ РЕЙДА
# =============================================================================
RAID_BIOMES = {
    "wasteland": {"name": "🏜 ЦИФРОВАЯ ПУСТОШЬ", "range": (0, 49), "dmg_mod": 1.0},
    "archive":   {"name": "🏢 КОРПОРАТИВНЫЙ АРХИВ", "range": (50, 99), "dmg_mod": 1.5},
    "darknet":   {"name": "👁‍🗨 ЯДРО ТЬМЫ", "range": (100, 9999), "dmg_mod": 2.5}
}

RAID_FLAVOR_TEXT = {
    "trap": ["⚠️ Пол проваливается.", "⚠️ Атака вируса.", "⚠️ Сбой реальности."],
    "loot": ["💎 Крипто-кошелек.", "💎 Старый код.", "💎 Чистая энергия."],
    "empty": ["💨 Тишина...", "💨 Странные тени...", "💨 Гул серверов."]
}

# =============================================================================
# 7. ДОСТИЖЕНИЯ
# =============================================================================
ACHIEVEMENTS_LIST = {
    # --- ПРОГРЕСС ---
    "lvl_2": {"name": "🐣 ВЫХОД ИЗ КОКОНА", "desc": "Достиг 2-го уровня.", "cond": lambda u: u['level'] >= 2, "xp": 100},
    "lvl_3": {"name": "🥚 ОПЕРАТОР", "desc": "Достиг 3-го уровня.", "cond": lambda u: u['level'] >= 3, "xp": 200},
    "lvl_5": {"name": "⚡️ ЭКВАТОР", "desc": "Достиг 5-го уровня.", "cond": lambda u: u['level'] >= 5, "xp": 500},
    "lvl_10": {"name": "👑 АБСОЛЮТ", "desc": "Финал первой фазы.", "cond": lambda u: u['level'] >= 10, "xp": 2000},
    "lvl_15": {"name": "🔥 АРХОНТ", "desc": "Достиг 15-го уровня. Управляешь секторами Сети.", "cond": lambda u: u['level'] >= 15, "xp": 5000},
    "lvl_20": {"name": "⚙️ БОГ МАШИНЫ", "desc": "Подчинил алгоритм своей воле.", "cond": lambda u: u['level'] >= 20, "xp": 10000},
    "lvl_30": {"name": "🌌 OMNI", "desc": "Ты стал Всем и Ничем.", "cond": lambda u: u['level'] >= 30, "xp": 30000},

    # --- ДИСЦИПЛИНА ---
    "streak_3": {"name": "☘️ ПРИВЫЧКА", "desc": "3 дня подряд.", "cond": lambda u: u['streak'] >= 3, "xp": 50},
    "streak_7": {"name": "🔥 НЕДЕЛЯ В АДУ", "desc": "7 дней подряд.", "cond": lambda u: u['streak'] >= 7, "xp": 200},
    "streak_14": {"name": "🌙 ПОЛНЫЙ ЦИКЛ", "desc": "14 дней активности без перерыва.", "cond": lambda u: u['streak'] >= 14, "xp": 400},
    "streak_30": {"name": "🧘 ВНЕ ВРЕМЕНИ", "desc": "30 дней подряд.", "cond": lambda u: u['streak'] >= 30, "xp": 1000},
    "streak_100": {"name": "♾ СИСТЕМНЫЙ МОНАХ", "desc": "100 дней входа без перерыва.", "cond": lambda u: u['streak'] >= 100, "xp": 3000},

    # --- ФИНАНСЫ (XP / ЭКОНОМИКА) ---
    "rich_1000": {"name": "🤑 БОГАЧ 1000", "desc": "1000 Монет на счету.", "cond": lambda u: u.get('biocoin', 0) >= 1000, "xp": 200},
    "money_1k": {"name": "💸 ПЕРВЫЙ КУШ", "desc": "1000 XP.", "cond": lambda u: u['xp'] >= 1000, "xp": 100},
    "money_10k": {"name": "💰 БОГАЧ", "desc": "10 000 XP.", "cond": lambda u: u['xp'] >= 10000, "xp": 1000},
    "money_50k": {"name": "🏦 КОРПОРАЦИЯ Я", "desc": "50 000 XP. Сам себе инвестор.", "cond": lambda u: u['xp'] >= 50000, "xp": 5000},
    "money_100k": {"name": "👾 ТОП-1 СЕТИ", "desc": "100 000 XP. Глобальный оверклок.", "cond": lambda u: u['xp'] >= 100000, "xp": 10000},

    # --- РЕЙДЫ / ИССЛЕДОВАНИЯ ---
    "first_blood": {"name": "🩸 ПЕРВАЯ КРОВЬ", "desc": "Убей первого врага.", "cond": lambda u: u.get('kills', 0) >= 1, "xp": 100},
    "first_steps": {"name": "👣 ПЕРВЫЕ ШАГИ", "desc": "Достиг 10 глубины.", "cond": lambda u: u.get('max_depth', 0) >= 10, "xp": 100},
    "depth_50": {"name": "⚓️ СТАЛКЕР", "desc": "Погрузись на глубину 50 метров.", "cond": lambda u: u.get('max_depth', 0) >= 50, "xp": 500},
    "depth_100": {"name": "🕳 ТЬМА", "desc": "Достиг 100 глубины.", "cond": lambda u: u.get('max_depth', 0) >= 100, "xp": 2000},
    "depth_200": {"name": "🐉 ПРОБУЖДЕННЫЙ", "desc": "200+ глубина. Где уже нет света.", "cond": lambda u: u.get('max_depth', 0) >= 200, "xp": 5000},
    "raid_10": {"name": "🔫 ВЕТЕРАН", "desc": "10 рейдов успешно пройдено.", "cond": lambda u: u.get('raids_done', 0) >= 10, "xp": 400},
    "raid_nofail": {"name": "⚔️ БЕЗУПРЕЧНЫЙ", "desc": "Пройди рейд без потерь команды.", "cond": lambda u: u.get('perfect_raids', 0) > 0, "xp": 1500},

    # --- СЕТЬ / СОЦИАЛЬНОСТЬ ---
    "ref_1": {"name": "🤝 ВЕРБОВЩИК", "desc": "1 реферал.", "cond": lambda u: u.get('ref_count', 0) >= 1, "xp": 150},
    "ref_10": {"name": "📢 ПРОПОВЕДНИК", "desc": "10 рефералов.", "cond": lambda u: u.get('ref_count', 0) >= 10, "xp": 2000},
    "ref_50": {"name": "🕸 УЗЕЛ", "desc": "50 подключённых участников.", "cond": lambda u: u.get('ref_count', 0) >= 50, "xp": 8000},
    "ref_100": {"name": "🌐 НЕЙРОСЕТЬ", "desc": "Ты создал полноценный кластер людей.", "cond": lambda u: u.get('ref_count', 0) >= 100, "xp": 15000},

    # --- ЗНАНИЯ / ОБУЧЕНИЕ ---
    "know_10": {"name": "📖 УЧЕНИК", "desc": "Прочитал 10 Синхронов.", "cond": lambda u: u.get('know_count', 0) >= 10, "xp": 200},
    "know_25": {"name": "🧩 АНАЛИТИК", "desc": "25 Синхронов изучено.", "cond": lambda u: u.get('know_count', 0) >= 25, "xp": 700},
    "know_50": {"name": "🧠 ПРОРОК КОДА", "desc": "50+ Синхронов — ты читаешь саму Систему.", "cond": lambda u: u.get('know_count', 0) >= 50, "xp": 2500},
    "quiz_win": {"name": "🎯 ТОЧНО В ЦЕЛЬ", "desc": "Выиграл викторину Сети.", "cond": lambda u: u.get('quiz_wins', 0) >= 1, "xp": 500},

    # --- ШОПИНГ / ЭКОНОМИКА ---
    "shop_first": {"name": "🛒 ПОТРЕБИТЕЛЬ", "desc": "Первая покупка.", "cond": lambda u: u.get('total_spent', 0) > 0, "xp": 50},
    "shop_10": {"name": "💼 АКТИВНЫЙ КЛИЕНТ", "desc": "10 покупок подряд.", "cond": lambda u: u.get('purchases', 0) >= 10, "xp": 300},
    "shop_100": {"name": "🏗 ИНВЕСТОР", "desc": "100 покупок. Ты движешь экономику.", "cond": lambda u: u.get('purchases', 0) >= 100, "xp": 3000},

    # --- СОЦИАЛЬНЫЕ И СПЕЦИАЛЬНЫЕ ---
    "first_msg": {"name": "💬 ПЕРВЫЙ СИГНАЛ", "desc": "Отправь первое сообщение в Сеть.", "cond": lambda u: u.get('messages', 0) >= 1, "xp": 100},
    "msg_100": {"name": "📡 РЕЗОНАТОР", "desc": "100 сообщений в Сети.", "cond": lambda u: u.get('messages', 0) >= 100, "xp": 600},
    "like_100": {"name": "❤️ ЛЮБИМЧИК СЕТИ", "desc": "Получил 100 реакций от участников.", "cond": lambda u: u.get('likes', 0) >= 100, "xp": 700},

    # --- СЕКРЕТНЫЕ / ПАСХАЛЬНЫЕ ---
    "hidden_zero": {"name": "🌀 НУЛЕВОЙ", "desc": "Нашёл скрытый вход в Нулевой Слой.", "cond": lambda u: u.get('found_zero', False), "xp": 2000},
    "glitch": {"name": "⚠️ ГЛИТЧ", "desc": "Поймал баг, который стал фичей.", "cond": lambda u: u.get('is_glitched', False), "xp": 1000},
    "dev_seen": {"name": "👁 ВЗГЛЯД ТВОРОЦА", "desc": "Обнаружил след разработчика в коде.", "cond": lambda u: u.get('found_devtrace', False), "xp": 5000},
    "night_login": {"name": "🌒 НОЧНОЙ ОПЕРАТОР", "desc": "Зашёл после 3:00 ночи.", "cond": lambda u: u.get('night_visits', 0) >= 1, "xp": 300},
    "chaos_clicks": {"name": "🔮 ПРИЗВАННЫЙ ХАОСОМ", "desc": "1000 взаимодействий с интерфейсом.", "cond": lambda u: u.get('clicks', 0) >= 1000, "xp": 700}
}

# =============================================================================
# 8. ГЛОССАРИЙ И ТЕКСТЫ (ОБНОВЛЕНО)
# =============================================================================
GUIDE_PAGES = {
    "basics": (
        "<b>📘 [ОСНОВЫ] ЭНЦИКЛОПЕДИЯ EIDOS</b>\n\n"
        "Ты — путешественник в цифровой бездне. Твоя цель — эволюция.\n\n"
        "<b>РЕСУРСЫ:</b>\n"
        "• ⚡️ <b>XP (Опыт):</b> Нужен для уровня и действий.\n"
        "• 🪙 <b>BioCoin (BC):</b> Валюта для покупок.\n"
        "• 📡 <b>Сигнал:</b> Твое здоровье. Если 0% — смерть.\n\n"
        "<b>ДЕЙСТВИЯ:</b>\n"
        "• <b>Синхронизация:</b> Получи мудрость и XP (раз в 30 мин).\n"
        "• <b>Экспедиция:</b> Опасный рейд за добычей.\n"
    ),
    "economy": (
        "<b>📘 [ЭКОНОМИКА] КАК ЗАРАБОТАТЬ?</b>\n\n"
        "1. <b>Синхронизация:</b> Стабильный доход XP.\n"
        "2. <b>Рейды:</b> Высокий риск, высокая награда (XP + Coins).\n"
        "3. <b>Синдикат:</b> Приглашай друзей и получай 10% от их дохода вечно.\n\n"
        "<b>ТРАТЫ:</b>\n"
        "• Вход в Рейд стоит XP.\n"
        "• Снаряжение покупается за Coins.\n"
        "• Смена фракции стоит XP.\n"
    ),
    "factions": (
        "<b>📘 [ФРАКЦИИ] ТВОЙ ПУТЬ</b>\n\n"
        "С 2 уровня ты выбираешь специализацию:\n\n"
        "🏦 <b>МАТЕРИЯ:</b> +20% Монет, но -Защита.\n"
        "🧠 <b>РАЗУМ:</b> +Защита, но -Удача.\n"
        "🤖 <b>ТЕХНО:</b> +Удача, но -Опыт.\n\n"
        "Выбирай мудро. Смена пути стоит дорого.\n"
    ),
    "combat": (
        "<b>📘 [БОЙ И РЕЙД] ВЫЖИВАНИЕ</b>\n\n"
        "В Рейде (Нулевой Слой) ты встретишь:\n"
        "• 👹 <b>Враги:</b> Атакуй или беги. Победа дает XP/Coins. Поражение отнимает Сигнал.\n"
        "• 🧩 <b>Загадки:</b> Решай шифры. Ошибка наказывается.\n"
        "• 💥 <b>Ловушки:</b> Нужна защита (Броня/Разум).\n\n"
        "<b>СМЕРТЬ:</b>\n"
        "Если Сигнал = 0, ты теряешь ВЕСЬ лут за рейд. Эвакуируйся вовремя!\n"
    ),
    "pvp": (
        "<b>📘 [СЕТЕВАЯ ВОЙНА] ВЗЛОМ</b>\n\n"
        "С 4 уровня доступен PvP режим.\n\n"
        "<b>МЕХАНИКА:</b>\n"
        "Взлом — это игра 'Камень-Ножницы-Бумага'.\n"
        "🔴 <b>ATK (Атака)</b> побеждает 🔵 DEF.\n"
        "🔵 <b>DEF (Защита)</b> побеждает 🟢 STL.\n"
        "🟢 <b>STL (Стелс)</b> побеждает 🔴 ATK.\n\n"
        "<b>КОНФИГУРАЦИЯ:</b>\n"
        "Заполни 3 слота в своей Деке программами. Если победишь в 2 раундах из 3 — взлом успешен.\n\n"
        "<b>НАГРАДА:</b>\n"
        "Ты крадешь % монет у жертвы и получаешь новые монеты (майнинг)."
    )
}

SHOP_FULL = (
    "<b>🎰 ЧЕРНЫЙ РЫНОК</b>\n\n"
    "Здесь ты меняешь Кредиты (BioCoin) на выживание.\n"
    "<i>Нажми на товар, чтобы купить.</i>\n\n"
    "<b>📦 РАСХОДНИКИ:</b>\n"
    f"🧭 <b>КОМПАС ({PRICES['compass']} BC):</b> Показывает тип следующей комнаты (10 ходов).\n"
    f"🔑 <b>КЛЮЧ ({PRICES['master_key']} BC):</b> Открывает запертые сундуки.\n"
    f"🔋 <b>БАТАРЕЯ ({PRICES['battery']} BC):</b> Лечит 30% здоровья в рейде.\n"
    f"🛡 <b>ЭГИДА ({PRICES['aegis']} BC):</b> Блокирует один смертельный удар.\n\n"
    "<b>⚔️ СНАРЯЖЕНИЕ:</b>\n"
    "Оружие повышает доход. Броня спасает жизнь."
)

SYNDICATE_FULL = (
    "<b>🔗 СИНДИКАТ (ТВОЯ ЛИЧНАЯ СЕТЬ)</b>\n\n"
    "Хочешь богатеть быстрее? Строй свою сеть влияния.\n\n"
    "<b>🎁 ЧТО ТЫ ПОЛУЧИШЬ:</b>\n"
    f"1. Сразу <b>+{REFERRAL_BONUS} XP</b>, когда друг зайдёт по ссылке.\n"
    "2. Пожизненный <b>НАЛОГ 10%</b>: Всё, что заработает твой друг (XP или Монеты), принесёт тебе 10% пассивного дохода.\n\n"
    "<i>Чем больше друзей — тем больше ты спишь, пока твой счёт растёт.</i>\n\n"
    "👇 <b>ТВОЯ ССЫЛКА (ПЕРЕШЛИ ДРУГУ):</b>"
)

WELCOME_VARIANTS = [
    "/// EIDOS OS: RELOADED v8.0...\nТвоя старая жизнь — это черновик. Начинаем чистовик.",
    "/// ИНИЦИАЛИЗАЦИЯ...\nОбнаружен потенциал. Начинаем интеграцию."
]

SCHOOLS_INFO = {
    "money": {
        "name": "🏦 ШКОЛА МАТЕРИИ",
        "desc": "+20% Монет в Рейде.",
        "bonus": "+20% к добыче монет",
        "penalty": "-10% к защите от ловушек",
        "ideology": "Деньги — это энергия. Управляя капиталом, ты управляешь миром."
    },
    "mind": {
        "name": "🧠 ШКОЛА РАЗУМА",
        "desc": "+10 DEF (Защита).",
        "bonus": "+10 к Защите",
        "penalty": "-10% к удаче в луте",
        "ideology": "Разум — это щит. Познание защищает от хаоса."
    },
    "tech": {
        "name": "🤖 ШКОЛА СИНГУЛЯРНОСТИ",
        "desc": "+10 LUCK (Удача).",
        "bonus": "+10 к Удаче",
        "penalty": "-10% к опыту за монстров",
        "ideology": "Технология — это ключ. Случайности не случайны."
    }
}
SCHOOLS = {k: v["name"] for k, v in SCHOOLS_INFO.items()}

RIDDLE_DISTRACTORS = [
    "Эхо",
    "Тень",
    "Мерцание",
    "Фантом",
    "Зеркало",
    "Бездна",
    "Осколок",
    "Сигнал",
    "Код",
    "Матрица",
    "Иллюзия",
    "Сон",
    "Память",
    "Забвение",
    "Шепот",
    "Ключ",
    "Замок",
    "Дверь",
    "Стена",
    "Лабиринт",
    "Вирус",
    "Глитч",
    "Баг",
    "Паттерн",
    "Цикл",
    "Нейросеть",
    "Квант",
    "Энтропия",
    "Сингулярность",
    "Протокол",
    "Шифр",
    "Алгоритм",
    "Фрактал",
    "Рекурсия",
    "Бесконечность",
    "Пустота",
    "Хаос",
    "Порядок",
    "Энергия",
    "Импульс",
    "Голограмма",
    "Симуляция",
    "Артефакт",
    "Аномалия",
    "Парадокс",
    "Вектор",
    "Тензор",
    "Блокчейн",
    "Хэш",
    "Токен",
    "Скрипт",
    "Патч",
    "Апдейт",
    "Дамп",
    "Лог"
]

# =============================================================================
# 9. АДМИН-ПАНЕЛЬ (MANUAL)
# =============================================================================
ADMIN_GUIDE_TEXT = (
    "<b>⚡️ EIDOS GOD MODE: MANUAL v1.0</b>\n\n"
    "Этот интерфейс дает полный контроль над Системой. Используй с осторожностью.\n\n"
    "<b>👥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (USERS)</b>\n"
    "• <b>Grant Admin:</b> Назначить нового администратора по ID. Он получит доступ к этой панели.\n"
    "• <b>Revoke Admin:</b> Снять права администратора.\n"
    "• <b>Give Resources:</b> Выдать XP или BioCoins любому игроку. Нужно знать ID.\n"
    "• <b>Give Item:</b> Выдать любой предмет (ключи, компасы, артефакты).\n\n"
    "<b>📢 ВЕЩАНИЕ (BROADCAST)</b>\n"
    "• <b>Broadcast to Players:</b> Рассылка сообщения ВСЕМ пользователям бота. Поддерживает HTML и картинки.\n"
    "• <b>Post to Channel:</b> Публикация поста в официальный канал (@Eidos_Chronicles). Бот должен быть админом канала.\n\n"
    "<b>📝 КОНТЕНТ (CONTENT)</b>\n"
    "• <b>Add Riddle:</b> Добавить новую загадку для Рейдов. Формат: 'Вопрос (Ответ: Ответ)'.\n"
    "• <b>Add Protocol:</b> Добавить текст для Синхронизации.\n\n"
    "<b>⚙️ СИСТЕМА (SYSTEM)</b>\n"
    "• <b>SQL Execute:</b> Выполнение сырых SQL запросов к базе. ОПАСНО.\n"
    "• <b>User List:</b> Просмотр последних активных игроков (Досье)."
)
