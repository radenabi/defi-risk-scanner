# defi-risk — DeFi Protocol Risk Scanner

AI-powered tool that scans DeFi protocols for risk factors and generates a risk score.

## Features

- Fetches on-chain data via Etherscan & DeFiLlama APIs
- Analyzes 8 risk factors: TVL, admin keys, contract verification, age, audits, centralization, oracle dependency, exploit history
- Risk scoring: A (safe) to F (critical)
- AI-powered deep analysis via MiMo API
- Markdown report output

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Scan a protocol by name
defi-risk scan uniswap

# Scan by contract address
defi-risk scan 0x1F98431c8aD98523631AE4a59f267346ea31F984 --chain ethereum

# Output as markdown
defi-risk scan aave --format markdown --output report.md

# With AI analysis
defi-risk scan compound --ai

# List supported protocols
defi-risk list
```

## Risk Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| TVL Concentration | 15% | Single wallet holds >50% of TVL |
| Admin Keys | 20% | Multisig vs EOA, timelock presence |
| Contract Verification | 10% | Source code verified on explorer |
| Protocol Age | 5% | Days since deployment |
| Audit Status | 15% | Number and quality of audits |
| Centralization | 15% | Upgradeability, pause functions |
| Oracle Dependency | 10% | External oracle reliance |
| Exploit History | 10% | Past hacks or incidents |

## Environment Variables

- `ETHERSCAN_API_KEY` — Etherscan API key (optional, higher rate limits)
- `MIMO_API_KEY` — MiMo API key for AI analysis

## License

MIT
