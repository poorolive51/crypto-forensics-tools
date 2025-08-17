import json
from bip_utils import (
    Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39Languages
)
from tronpy.keys import PrivateKey as TronPrivateKey

# Configuration
mnemonics_file = "mnemonics.json"  # Source file with seed phrases
txt_output_file = "tron_addresses.txt"  # Plain text output (addresses only)

# Data structure for deduplication
unique_addresses = set()

try:
    # Open input and output files
    with open(mnemonics_file, 'r') as infile, \
            open(txt_output_file, 'w') as txt_outfile:
        
        # Load mnemonics from JSON file
        data = json.load(infile)

        # Process each mnemonic in the input file
        for entry in data:
            mnemonic_phrase = entry.get("mnemonic", "").strip()
            if not mnemonic_phrase:
                continue

            try:
                # Generate seed from mnemonic phrase
                seed_bytes = Bip39SeedGenerator(mnemonic_phrase, Bip39Languages.ENGLISH).Generate()

                # Derive TRON private key using BIP44 derivation path
                # Path: m/44'/195'/0'/0/0 (TRON standard)
                bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
                bip44_addr_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
                private_key_bytes = bip44_addr_ctx.PrivateKey().Raw().ToBytes()

                # Generate TRON address from private key
                tron_private_key = TronPrivateKey(private_key_bytes)
                tron_public_key = tron_private_key.public_key
                tron_address = tron_public_key.to_base58check_address()

                # Store only unique addresses
                if tron_address not in unique_addresses:
                    unique_addresses.add(tron_address)

            except Exception as e:
                print(f"Error processing mnemonic '{mnemonic_phrase}': {e}")

    # Write all unique addresses to plain text file
    for address in sorted(unique_addresses):
        txt_outfile.write(f"{address}\n")

except FileNotFoundError:
    print(f"Error: JSON file '{mnemonics_file}' not found.")
except json.JSONDecodeError:
    print(f"Error: Failed to decode JSON in '{mnemonics_file}'.")
except ImportError:
    print("Error: Required libraries ('bip-utils' or 'tronpy') not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
