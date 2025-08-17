# Crypto Forensics: Python Tools for Tracking Seed Phrase Scammers

This repository contains Python scripts designed to help track "steal-your-gas" cryptocurrency scammers by analyzing YouTube comments for seed phrases, converting them to wallet addresses, and visualizing transaction activity on the TRON blockchain.

This project accompanies the blog post: [CRYPTO FORENSICS: HOW TO TRACK SEED PHRASE SCAMMERS WITH PYTHON](https://medium.com/@poorolive51/crypto-forensics-python-tools-for-tracking-seed-phrase-scammers-571570c9b234)

## The "Steal-Your-Gas" Scam

The "steal-your-gas" scam (or seed phrase scam) is a common deception where scammers post messages containing crypto wallet seed phrases on public platforms like YouTube comments, Reddit, and Twitter. These messages falsely claim that the seed phrase grants access to a wallet holding significant amounts of cryptocurrency.

Victims who attempt to "steal" these funds by logging in with the provided seed phrase find that there isn't enough "gas" (transaction fees) in the wallet's native currency to transfer the tokens. When victims transfer a small amount of gas (typically $10-$30) to the wallet, these funds are immediately siphoned off by an automated script. Furthermore, these scam wallets are often multi-signature, meaning victims could never have transferred the funds out anyway, as multiple signatures are required for any transaction.

This project provides tools to investigate such scam activities.

## Prerequisites

Before you begin, ensure you have the following:

*   **Intermediate Python knowledge:** Familiarity with Python programming.
*   **Basic understanding of cryptocurrency wallets and transactions:** Knowledge of how seed phrases, private keys, and blockchain transactions work.
*   **YouTube Data API v3 Key:** Obtain a free API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
*   **TRONSCAN API Key:** Obtain a free API key from [Tronscan](https://tronscan.org/api-keys).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/crypto-forensics-tools.git
    cd crypto-forensics-tools
    ```
    *(Note: You will need to create a new GitHub repository and push this code to it after I've finished creating the files.)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    Create a file named `.env` in the root directory of the project and add your API keys as follows:

    ```
    YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY"
    TRONSCAN_API_KEY="YOUR_TRONSCAN_API_KEY"
    ```
    Replace `"YOUR_YOUTUBE_API_KEY"` and `"YOUR_TRONSCAN_API_KEY"` with your actual API keys.

## Project Workflow and Usage

This project follows a three-step process to identify and analyze scammer activity:

### Step 1: Search YouTube for Scammer Comments with Seed Phrases

The `youtube_seed_phrase_scanner.py` script searches YouTube for videos related to cryptocurrency and extracts potential seed phrases from their comments.

**How to run:**
```bash
python youtube_seed_phrase_scanner.py
```

**What it does:**
*   Searches YouTube for a predefined set of crypto-related search terms (e.g., "crypto tron", "okx wallet crypto", "ethereum wallet").
*   Retrieves comments from the top 5 videos for each search term.
*   Uses advanced pattern matching to identify 12-word seed phrases within the comments.
*   Outputs unique seed phrases along with their source (author, video ID, timestamp) to `mnemonics.json`.

**Output:**
*   `mnemonics.json`: A JSON file containing a list of unique seed phrases found, along with metadata about where they were found.

### Step 2: Convert Seed Phrases to Wallet Addresses

The `tron_address_generator.py` script takes the extracted seed phrases and converts them into TRON wallet addresses.

**How to run:**
```bash
python tron_address_generator.py
```

**What it does:**
*   Reads seed phrases from `mnemonics.json`.
*   Uses the `bip-utils` library to derive TRON private keys and then TRON addresses from these seed phrases (using the BIP44 derivation path: `m/44'/195'/0'/0/0`).
*   Writes all unique TRON addresses to `tron_addresses.txt`.

**Output:**
*   `tron_addresses.txt`: A plain text file, with each line containing a unique TRON wallet address.

### Step 3: Analyze Transaction Activity

The `tron_transaction_analyzer.py` script fetches and visualizes the transaction history for the generated TRON addresses.

**How to run:**
```bash
python tron_transaction_analyzer.py
```
The script will prompt you to enter the filename containing TRON addresses (e.g., `tron_addresses.txt`).

**What it does:**
*   Connects to the Tronscan API (with a built-in rate limiter to avoid throttling).
*   Retrieves all TRC20 (specifically USDT) token transfers for each address.
*   Generates an interactive Plotly scatter plot visualizing incoming and outgoing USDT transactions over time for each wallet. The size of the points on the plot is proportional to the transaction amount.

**Output:**
*   An interactive HTML plot displayed in your default web browser, showing the transaction timeline.

## Next Steps

This project provides a foundation for further analysis. Here are some ideas for expansion:

*   **Common Transfer Recipients:** Analyze transaction data to identify frequently recurring recipient addresses.
*   **Signatory Analysis:** Investigate the number of signatories required for transactions on multi-signature wallets.
*   **Network Graph:** Create a network visualization of senders and recipients to map the flow of funds.
*   **Downstream Recipients:** Identify major recipients of funds from these scammer wallets.
*   **Cross-Chain Analysis:** Combine this dataset with information from other blockchains (e.g., Ethereum, Binance Smart Chain) to uncover cross-chain scam patterns.

## Get the Code

All scripts mentioned in this tutorial are available in this repository.

## Contact

For questions or feedback, you can reach out to poorolive51@gmail.com.
